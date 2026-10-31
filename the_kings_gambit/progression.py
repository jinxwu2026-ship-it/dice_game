"""Fixed encounters and extra-life progression, without dice calculations."""

import time
import random
import json

from the_kings_gambit.battle import _validate_ai_delay, _validate_score_ambition, run_match
from the_kings_gambit.models import MatchState, RunState, Die, QUALITIES, validate_roster
from the_kings_gambit.dice import PRICES, die_label, face_distribution, roll_item
from the_kings_gambit.ui import read_input, show_run_summary, show_panel, roster_text, inspect_dice, event_story, present
from the_kings_gambit.run_score import calculate_run_score

ENCOUNTERS = (
    {"kind": "Common", "ai_type": "easy"},
    {"kind": "Common", "ai_type": "conservative"},
    {"kind": "Common", "ai_type": "aggressive"},
    {"kind": "Elite", "ai_type": "neutral"},
    {"kind": "Boss", "ai_type": "composite"},
)

WEIGHTED_KINDS = ("lucky", "two", "odd", "even")
SPECIAL_KINDS = WEIGHTED_KINDS + ("momentum",)  # Fixed-Silver kinds enter only the Silver pool.
INITIAL_RESCUE_CHANCE = 20
WIN_BONUSES = (200, 200, 250, 350, 500)
CASH_CAPS = (100, 150, 150, 200, 300)
SPINNER = {"gain_die": 35, "gain_coins": 25, "lose_die": 10,
           "lose_coins": 10, "lose_life": 10, "nothing": 10}


def _pick(items, source):
    return items[source.randint(0, len(items) - 1)]


def create_special(run, quality, source, kind=None, exclude=()):
    """Reserve a unique when generated, even if later refused or left in a shop."""
    if quality not in QUALITIES:
        raise ValueError("unknown special quality")
    choices = [k for k in SPECIAL_KINDS if k not in exclude]
    if quality == "silver":
        if "rescue" not in exclude:
            choices.append("rescue")
        choices += [k for k in ("devil", "angel")
                    if k not in run.spawned_unique and k not in exclude
                    and not any(d.kind == k for d in run.dice)]
    if kind is None:
        kind = _pick(choices, source)
    elif kind not in choices:
        raise ValueError("this die is unavailable or already generated")
    die = Die(kind, quality)
    if kind in ("devil", "angel"):
        run.spawned_unique.add(kind)
    return die


def make_encounter(run, stage, source):
    if not isinstance(stage, int) or isinstance(stage, bool) or not 0 <= stage < 5:
        raise ValueError("stage must be 0..4")
    if stage == 0:
        qualities, main = ["bronze"], "bronze"
    elif stage in (1, 2):
        ticket = source.randint(0, 99)
        qualities = ["silver", "bronze"] if ticket < 50 else ["bronze", "bronze"]
        main = "silver" if ticket < 30 else "bronze"
    elif stage == 3:
        ticket = source.randint(0, 99)
        qualities = (["gold", "silver", "bronze"] if ticket < 10 else
                     ["silver", "silver", "bronze"] if ticket < 55 else
                     ["silver", "bronze", "bronze"])
        main = "gold" if ticket < 10 else "silver"
    else:
        qualities, main = ["gold", "silver", "bronze", "bronze"], "gold"
    dice = []
    for quality in qualities:
        dice.append(create_special(run, quality, source, exclude={d.kind for d in dice}))
    dice += [Die() for _ in range(6 - len(dice))]
    return dice, next(d for d in dice if d.quality == main)


def merge_preview(dice, pending, slot):
    """Plan a merge without changing inventory or money; cancellation stays safe."""
    if not isinstance(slot, int) or isinstance(slot, bool) or not 0 <= slot < 6:
        raise ValueError("choose a slot from 1 to 6")
    old = dice[slot]
    if not can_merge(old, pending):
        raise ValueError("merge requires matching non-unique Bronze or Silver dice")
    planned = list(dice)
    planned[slot] = Die()
    return planned, Die(old.kind, QUALITIES[QUALITIES.index(old.quality) + 1])


def can_merge(first, second):
    return (first.kind == second.kind and first.quality == second.quality
            and first.kind in SPECIAL_KINDS and first.quality in ("bronze", "silver"))


def equipped_merges(dice):
    return [(i + 1, j + 1) for i in range(6) for j in range(i + 1, 6)
            if can_merge(dice[i], dice[j])]


def die_wager_choices(dice, opponent, main):
    """Return actual same-quality stakes allowed below the main stake."""
    choices = {}
    for slot, die in enumerate(dice, 1):
        if die.quality == "basic" or QUALITIES.index(die.quality) > QUALITIES.index(main.quality):
            continue
        candidates = [d for d in opponent if d.quality == die.quality]
        if candidates:
            choices[slot] = main if main in candidates else candidates[0]
    return choices


def merge_equipped(run, first, second):
    """Merge two equipped items outside combat; keep the result in second slot."""
    if (not isinstance(second, int) or isinstance(second, bool)
            or not 0 <= second < 6 or first == second):
        raise ValueError("choose two different slots from 1 to 6")
    planned, result = merge_preview(run.dice, run.dice[second], first)
    planned[second] = result
    validate_roster(planned)
    run.dice = planned


def settle_wager(run, wager, winner, stage):
    """Settle once. Return the actual AI prize object, never generate a new die."""
    if wager.get("settled") or winner not in ("Player", "Opponent", None):
        raise ValueError("invalid or already settled wager")
    prize = None
    if wager["mode"] == "cash":
        if winner in ("Player",None):
            run.coins += wager["amount"]  # Returning principal is not earned income.
        if winner == "Player":
            gain_coins(run,wager["amount"],"cash wager")
    elif winner == "Player":
        prize = wager["opponent"]
    elif winner == "Opponent":
        slot = next(i for i, die in enumerate(run.dice) if die.serial == wager["player"].serial)
        run.dice[slot] = Die()
    if winner == "Player":
        gain_coins(run,WIN_BONUSES[stage],"victory bonus")
    wager["settled"] = True
    return prize


def gain_coins(run, amount, source):
    run.coins += amount
    if amount:
        run.score_history.append(dict(event="COINS_EARNED",amount=amount,source=source))


def event_result(run, input_func, output_func, **data):
    """Keep a window result readable; terminal results need no extra prompt."""
    if not present(output_func,"event_result",run=run,**data):
        show_panel([data["message"]],output_func)
        return True
    while True:
        command = read_input("Enter: continue; Q: quit: ",input_func)
        if command == "":
            return True
        if command in ("q","quit"):
            if run.is_active:
                run.status = "quit"
            return False


def _ask(run, lines, prompt, input_func, output_func, other_dice=None, view=None):
    if view is not None:
        story = event_story(view["screen"],run)
        view = dict(view, run=run,story=story)
        if story:
            lines = [story]+lines
    show_panel([f"Coins: {run.coins}  HP(extra lives): {run.hp}", roster_text(run.dice)] + lines,
               output_func, view=view)
    while True:
        command = read_input(prompt, input_func)
        if inspect_dice(run, command, output_func, other_dice):
            continue
        if command in ("q", "quit"):
            # A completed Boss win stays a win if its optional prize is abandoned.
            if run.status != "victory":
                run.status = "quit"
            return None
        return command


def placement_slots(dice, pending):
    allowed = []
    for slot in range(6):
        planned = list(dice)
        planned[slot] = pending
        try:
            validate_roster(planned)
            allowed.append(slot+1)
        except ValueError:
            pass
    return allowed


def receive_die(run, original, source_name, input_func, output_func, record, cost=0, batch=None):
    """Preview merges/replacements; commit money and inventory together."""
    planned, pending = list(run.dice), original
    message = ""
    while True:
        cash = PRICES[original.quality] * 4 // 5 if source_name == "battle" else 0
        refuse = f"D: decline for {cash} coins" if source_name == "battle" else "D: decline/cancel (no coins)"
        label = f"{source_name.upper()} DIE"+(f" {batch[0]}/{batch[1]}" if batch else "")
        command = _ask(run, [f"{label}: {pending.kind} {pending.quality} (ID {pending.serial})",
                             "1..6: replace slot | M slot: merge, then place result", refuse,
                             "Preview: " + roster_text(planned), message], "Reward choice: ", input_func, output_func,
                       view=dict(screen="reward", die=pending, planned=planned, source=source_name,
                                 cashout=cash, cost=cost, message=message,
                                 batch=batch,
                                 placement_slots=placement_slots(planned,pending),
                                 merge_slots=[i+1 for i, die in enumerate(planned) if can_merge(die, pending)]))
        if command is None:
            record("REWARD_ABANDONED", f"{source_name}, ID {original.serial}; no inventory change")
            return False
        if command in ("d", "decline", "skip"):
            gain_coins(run,cash,"battle die cashout")
            record("REWARD_DECLINED", f"{source_name}, ID {original.serial}; coins +{cash}")
            return False
        try:
            if command.startswith("m "):
                slot = int(command[2:]) - 1
                planned, pending = merge_preview(planned, pending, slot)
                message = "Merge preview only. Choose a slot to keep the result, or merge again."
                continue
            slot = int(command) - 1
            if not 0 <= slot < 6:
                raise ValueError("slot must be 1..6")
            result = list(planned)
            result[slot] = pending
            validate_roster(result)
            if cost > run.coins:
                raise ValueError("not enough coins")
            run.dice = result
            run.coins -= cost
            run.score_history.append(dict(event="DIE_ACQUIRED",serial=original.serial,
                                          quality=original.quality,source=source_name))
            record("REWARD_KEPT", f"{source_name}: item {original.serial} -> {pending.serial}, "
                   f"slot {slot+1}, paid {cost}; {[(d.serial,d.kind,d.quality) for d in result]}")
            return True
        except ValueError as error:
            message = f"Invalid reward choice: {error}"


def _initial_reward(run, source, input_func, output_func, record):
    while True:
        command = _ask(run, ["INITIAL DRAW: three different Bronze special dice.",
                             f"{INITIAL_RESCUE_CHANCE}%: replace one Bronze with a Silver Rescue.",
                             "Enter/P: draw | S: skip | Q: quit"], "Initial draw: ", input_func, output_func,
                       view=dict(screen="initial",rescue_chance=INITIAL_RESCUE_CHANCE))
        if command is None or command in ("s", "skip"):
            record("INITIAL_SKIPPED", "Initial reward skipped.")
            return
        if command not in ("", "p", "play"):
            continue
        break
    kinds = list(SPECIAL_KINDS)
    chosen = []
    for _ in range(3):
        kind = _pick(kinds,source)
        kinds.remove(kind)
        chosen.append(kind)
    if source.randint(0,99) < INITIAL_RESCUE_CHANCE:
        chosen[source.randint(0,2)] = "rescue"
    dice = [create_special(run,"silver" if kind == "rescue" else "bronze",source,kind) for kind in chosen]
    record("INITIAL_DRAW",str([(die.serial,die.kind,die.quality) for die in dice]))
    for index,die in enumerate(dice,1):
        receive_die(run,die,"initial",input_func,output_func,record,batch=(index,3))
        if not run.is_active:
            return


def _choose_wager(run, stage, opponent, main, input_func, output_func, record):
    message = ""
    while True:
        choices = die_wager_choices(run.dice, opponent, main)
        command = _ask(run, ["WAGER: " + ENCOUNTERS[stage]["ai_type"],
                             "Opponent: " + roster_text(opponent),
                             f"Main stake: {main.kind} {main.quality} (ID {main.serial})",
                             f"C amount: cash, step 50, max {CASH_CAPS[stage]} | D your-slot: die wager",
                             "M a b: merge two equipped dice free before wagering",
                             "Enter: wager 0 cash. Both sides use their equipped dice.", message],
                       "Wager: ", input_func, output_func, other_dice=opponent,
                       view=dict(screen="wager", stage=stage+1, encounter=ENCOUNTERS[stage],
                                 main=main, opponent=opponent, choices=choices,
                                 cash_amounts=list(range(0, min(run.coins, CASH_CAPS[stage])+1, 50)),
                                 bonus=WIN_BONUSES[stage], cap=CASH_CAPS[stage],
                                 merges=equipped_merges(run.dice), message=message))
        if command is None:
            return None
        try:
            if command.startswith("m "):
                _, first, second = command.split()
                merge_equipped(run, int(first)-1, int(second)-1)
                record("DICE_MERGED", f"Equipped slots {first}, {second}; result in {second}")
                message = "Merge complete. Choose your wager."
                continue
            if command == "":
                command = "c 0"
            mode, value = command.split()
            value = int(value)
            if mode in ("c", "cash"):
                if value < 0 or value % 50 or value > min(run.coins, CASH_CAPS[stage]):
                    raise ValueError("cash must be an affordable multiple of 50 within this stage's cap")
                wager = {"mode": "cash", "amount": value, "settled": False}
                run.coins -= value
            elif mode in ("d", "die"):
                if not 1 <= value <= 6:
                    raise ValueError("choose your slot 1..6")
                die = run.dice[value-1]
                if value not in choices:
                    raise ValueError("both sides need an actual matching quality at or below the main stake")
                prize = choices[value]
                wager = {"mode": "die", "player": die, "opponent": prize, "settled": False}
            else:
                raise ValueError("use C amount or D slot")
            record("WAGER_START", str(wager))
            return wager
        except ValueError as error:
            message = f"Invalid wager: {error}"


def guess_event(run, source, input_func, output_func, record):
    while True:
        command = _ask(run, ["GUESS SIZE: Enter/P starts; S skips. Up to three guesses.",
                             "Rewards: Silver die, then +100, then +200. A miss loses pending prizes."],
                       "Guess event: ", input_func, output_func, view=dict(screen="guess_intro"))
        if command is None or command in ("s", "skip"):
            record("GUESS_SKIPPED", "No pending rewards.")
            return
        if command in ("", "p", "play"):
            break
    # Wild faces have no standalone number; only biased dice are event-compatible.
    die = create_special(run, "silver", source, kind=_pick(WEIGHTED_KINDS, source))
    coins = 0
    for attempt in range(3):
        current = die if attempt == 0 else Die()
        small = sum(p for face, p in face_distribution(current.kind, current.quality) if 1 <= face <= 3)
        while True:
            command = _ask(run, [f"GUESS {attempt+1}/3: {current.kind} {current.quality}",
                                 f"Small 1-3: {small:.1%}; Big 4-6: {1-small:.1%}",
                                 f"Pending: Silver die + {coins} coins. S: small | B: big"],
                           "Your guess: ", input_func, output_func,
                           view=dict(screen="guess", attempt=attempt+1, die=current, prize=die,
                                     small=small, pending_coins=coins))
            if command is None:
                record("GUESS_QUIT", "Pending prizes abandoned.")
                return
            if command in ("s", "small", "b", "big"):
                break
        face = roll_item(current, source)
        correct = (face <= 3) == (command in ("s", "small"))
        present(output_func,"guess_roll",run=run,die=current,face=face,attempt=attempt+1,
                correct=correct,guess="Small" if command in ("s","small") else "Big")
        record("GUESS_ROLL", f"Attempt {attempt+1}, guess={command}, face={face}, correct={correct}")
        if not correct:
            run.notice = f"Guess rolled {face}: miss, pending prizes lost. Existing assets unchanged."
            event_result(run,input_func,output_func,event_type="guess",die=current,face=face,
                         correct=False,attempt=attempt+1,message=run.notice)
            return
        coins += (0, 100, 200)[attempt]
        if attempt < 2:
            while True:
                command = _ask(run, [f"Rolled {face}: correct! Pending Silver + {coins} coins.",
                                     "B: claim and stop | R: risk all pending prizes on the next guess"],
                               "Claim or continue: ", input_func, output_func,
                               view=dict(screen="guess_claim", attempt=attempt+1, face=face,
                                         die=current,prize=die, pending_coins=coins))
                if command is None:
                    record("GUESS_QUIT", "Pending prizes abandoned.")
                    return
                if command in ("b", "bank", "r", "roll"):
                    break
            if command in ("r", "roll"):
                continue
        elif not event_result(run,input_func,output_func,event_type="guess",die=current,face=face,
                              correct=True,attempt=attempt+1,message=f"Three correct! Silver die +{coins} coins."):
            return
        gain_coins(run,coins,"guess event")
        run.notice = f"Guess claimed Silver +{coins} coins."
        record("GUESS_CLAIM", f"Silver item {die.serial}, coins +{coins}")
        receive_die(run, die, "guess", input_func, output_func, record)
        return


def spinner_event(run, source, input_func, output_func, record):
    remaining = dict(SPINNER)
    for attempt in range(3):
        total = sum(remaining.values())
        while True:
            lines = [f"SPINNER {attempt+1}/3. Enter/P: spin | S: stop/skip.", run.notice]
            lines += [f"{name}: {weight/total:.1%}" for name, weight in remaining.items()]
            if run.hp == 0:
                lines += ["WARNING: lose_life ends this run immediately."]
            command = _ask(run, lines, "Spinner: ", input_func, output_func,
                           view=dict(screen="spinner", attempt=attempt+1, remaining=remaining,
                                     message=run.notice))
            if command is None or command in ("s", "skip", "stop"):
                record("SPINNER_STOP", f"Stopped after {attempt} draws.")
                return
            if command in ("", "p", "play"):
                break
        ticket = source.randint(1, total)
        for item, weight in remaining.items():
            ticket -= weight
            if ticket <= 0:
                break
        wheel = dict(remaining)
        present(output_func,"spinner_roll",run=run,remaining=wheel,chosen=item,attempt=attempt+1)
        del remaining[item]
        details = item
        lost_die = False
        coins_before,hp_before = run.coins,run.hp
        if item == "gain_die":
            quality = "silver" if source.randint(0, 99) < 30 else "bronze"
            die = create_special(run, quality, source)
        elif item == "gain_coins":
            gain_coins(run,200,"spinner")
        elif item == "lose_coins":
            run.coins = max(0, run.coins - 150)
        elif item == "lose_die":
            slots = [i for i, die in enumerate(run.dice) if die.kind != "basic"]
            if slots:
                slot = _pick(slots, source)
                details += f" item {run.dice[slot].serial}"
                run.dice[slot] = Die()
                lost_die = True
        elif item == "lose_life":
            if run.hp:
                run.hp -= 1
            else:
                run.status = "defeat"
                run.end_reason = "Spinner cost the final life."
        record("SPINNER_DRAW", details + f"; remaining weights={remaining}")
        flavour = {"gain_die":"The wheel offers a stranger's die.","gain_coins":"A purse falls from the wheel.",
                   "lose_coins":"The wheel demands its toll.",
                   "lose_die":"A die vanishes into the shadows." if lost_die else "The shadows find no special die to take.",
                   "lose_life":"The ward cracks." if run.is_active else "Without a ward, the curse ends your journey.",
                   "nothing":"The wheel falls silent."}[item]
        run.notice = f"{flavour} Coins {coins_before} -> {run.coins}. Wards {hp_before} -> {run.hp}."
        if not event_result(run,input_func,output_func,event_type="spinner",remaining=wheel,
                            chosen=item,attempt=attempt+1,message=run.notice):
            return
        if item == "gain_die":
            receive_die(run, die, "spinner", input_func, output_func, record)
        if not run.is_active:
            return


def shop_stock(run, source):
    qualities = (["gold", "silver", "silver"] if source.randint(0, 1) else ["silver"] * 3) + ["bronze"] * 3
    return [create_special(run, quality, source) for quality in qualities]


def shop_event(run, source, input_func, output_func, record):
    stock = shop_stock(run, source)
    refreshed = serviced = False
    message = ""
    while run.is_active:
        lines = ["SHOP: buy N | refresh (200, once) | upgrade slot (300) | remove slot (50)",
                 "M a b: free equipped merge. Upgrade/remove share ONE service.",
                 "Enter/leave: Boss. No selling or refunds."]
        lines += [f"{i}: {die.kind} {die.quality}, {PRICES[die.quality]} coins" if die else f"{i}: SOLD"
                  for i, die in enumerate(stock, 1)]
        lines += [message]
        command = _ask(run, lines, "Shop: ", input_func, output_func,
                       view=dict(screen="shop", stock=stock, refreshed=refreshed, serviced=serviced,
                                 upgrade_slots=[i+1 for i,d in enumerate(run.dice)
                                                if d.quality == "bronze" and d.kind in SPECIAL_KINDS],
                                 remove_slots=[i+1 for i,d in enumerate(run.dice) if d.kind != "basic"],
                                 merges=equipped_merges(run.dice), message=message))
        if command is None or command in ("", "leave", "l"):
            record("SHOP_END", "Leaving shop.")
            return
        try:
            if command.startswith("m "):
                _, first, second = command.split()
                merge_equipped(run, int(first)-1, int(second)-1)
                record("DICE_MERGED", f"Equipped slots {first}, {second}; result in {second}")
                message = "Merge complete; paid service still available."
                continue
            if command in ("refresh", "r"):
                if refreshed or run.coins < 200:
                    raise ValueError("refresh unavailable or unaffordable")
                run.coins -= 200
                stock = shop_stock(run, source)
                refreshed = True
                record("SHOP_REFRESH", "Paid 200; six new items, purchased dice retained.")
                continue
            action, number = command.split()
            slot = int(number) - 1
            if not 0 <= slot < 6:
                raise ValueError("slot must be 1..6")
            if action == "buy":
                die = stock[slot]
                if die is None or run.coins < PRICES[die.quality]:
                    raise ValueError("item sold or unaffordable")
                if receive_die(run, die, "shop", input_func, output_func, record, PRICES[die.quality]):
                    stock[slot] = None
            elif action in ("upgrade", "remove"):
                cost = 300 if action == "upgrade" else 50
                die = run.dice[slot]
                if serviced or run.coins < cost or die.kind == "basic":
                    raise ValueError("service unavailable or unaffordable")
                if action == "upgrade" and (die.quality != "bronze" or die.kind not in SPECIAL_KINDS):
                    raise ValueError("only a non-unique Bronze die can use this service")
                run.dice[slot] = Die(die.kind, "silver") if action == "upgrade" else Die()
                run.coins -= cost
                serviced = True
                record("SHOP_SERVICE", f"{action} slot {slot+1}, paid {cost}")
            else:
                raise ValueError("unknown shop command")
            message = ""
        except ValueError as error:
            message = f"Invalid shop command: {error}"


def finish_encounter(run, match):
    """Apply one completed match once; zero extra lives still allows playing."""
    if not isinstance(run, RunState) or not run.is_active:
        raise ValueError("the run has already ended")
    if (not isinstance(match, MatchState) or not match.against_ai
            or match.target != run.target or match.winner not in ("Player", "Opponent")
            or match.scores[match.winner] < match.target):
        raise ValueError("finish a valid opponent match before updating the run")
    if any(result["match"] is match for result in run.history):
        raise ValueError("this match has already been applied")
    boss = run.encounter_index == len(ENCOUNTERS) - 1
    lost = match.winner == "Opponent"
    previous_hp = run.hp
    if lost:
        if run.hp == 0 or boss:
            run.status = "defeat"
        if run.hp > 0:
            run.hp -= 1
    elif boss:
        run.status = "victory"
    stage = run.encounter_index + 1
    run.history.append({"stage": stage, "ai_type": ENCOUNTERS[stage - 1]["ai_type"],
                        "winner": match.winner, "scores": dict(match.scores),
                        "hp_before": previous_hp, "hp_after": run.hp, "match": match})
    if not lost:
        run.score_history.append(dict(event="STAGE_WON",stage=stage))
    if run.is_active:
        run.encounter_index += 1


def run_campaign(input_func=input, output_func=print, random_source=None,
                  score_ambition=500, ai_delay=2, sleep_func=time.sleep,
                  log_func=None, target=2000):
    """Play the fixed sequence, wagers, events and one shop with shared dice rules."""
    _validate_score_ambition(score_ambition)
    _validate_ai_delay(ai_delay)
    run = RunState(target)
    source = random_source if random_source is not None else random
    wager = None

    def record(event, details, stage=None):
        if log_func is not None:
            stage = run.encounter_index + 1 if stage is None else stage
            log_func(f"Event: {event} | Stage: {stage}/5 | "
                     f"HP (extra lives): {run.hp} | Status: {run.status}\n"
                     f"Coins: {run.coins} | Inventory: {[(d.serial,d.kind,d.quality) for d in run.dice]}\n"
                     f"Details: {details}\n\n")

    record("RUN_START", "Fixed five stages. HP=1 is one extra life; HP=0 is the final life.")
    try:
        _initial_reward(run, source, input_func, output_func, record)
        while run.is_active:
            stage_index = run.encounter_index
            stage = stage_index + 1
            encounter = ENCOUNTERS[stage_index]
            opponent, main = make_encounter(run, stage_index, source)
            context = (f"Stage: {stage}/5 | {encounter['kind']} | AI: {encounter['ai_type']} | "
                       f"HP (extra lives): {run.hp}")
            record("STAGE_START", context + f"; opponent={[(d.serial,d.kind,d.quality) for d in opponent]}")
            wager = _choose_wager(run, stage_index, opponent, main, input_func, output_func, record)
            if wager is None:
                break
            context += f" | Coins: {run.coins} | Wager: {wager['mode']}"
            match = run_match(input_func=input_func, output_func=output_func,
                              random_source=source, score_ambition=score_ambition,
                              ai_delay=ai_delay, sleep_func=sleep_func, target=run.target,
                              log_func=log_func, ai_type=encounter["ai_type"], run_context=context,
                              rosters={"Player": tuple(run.dice), "Opponent": tuple(opponent)},
                              event_func=lambda event: run.score_history.append(dict(event,stage=stage)))
            prize = settle_wager(run, wager, match.winner, stage_index)
            record("WAGER_END", f"winner={match.winner}, wager={wager}", stage)
            if match.winner is None:
                run.status = "quit"
                break
            finish_encounter(run, match)
            message = (f"Stage {stage}: {match.winner} wins. "
                       f"Scores Player={match.scores['Player']}, Opponent={match.scores['Opponent']}. "
                       f"HP (extra lives): {run.hp}.")
            record("STAGE_END", message + f" Victory bonus={WIN_BONUSES[stage_index] if match.winner == 'Player' else 0}", stage)
            if prize is not None:
                receive_die(run, prize, "battle", input_func, output_func, record)
            if stage_index == 4 and match.winner == "Player" and (prize is None or prize.quality != "gold"):
                record("BOSS_BOUNTY",f"Guaranteed Gold: item {main.serial}")
                receive_die(run,main,"battle",input_func,output_func,record)
            if not run.is_active:
                break
            if stage_index == 0:
                guess_event(run, source, input_func, output_func, record)
            elif stage_index == 2:
                spinner_event(run, source, input_func, output_func, record)
            elif stage_index == 3:
                shop_event(run, source, input_func, output_func, record)
            if not run.is_active:
                break
            message += " " + run.notice + f" Next: stage {run.encounter_index + 1}. Enter to continue; Q to quit."
            show_run_summary(run, message, output_func)
            while True:
                command = read_input("Press Enter for the next stage, or Q to quit: ", input_func)
                if command in ("q", "quit"):
                    run.status = "quit"
                    break
                if command == "":
                    break
                show_run_summary(run, "Invalid command. Press Enter or Q.", output_func)
    except KeyboardInterrupt:
        if wager is not None and not wager["settled"]:
            settle_wager(run, wager, None, run.encounter_index)
        if run.status != "victory":
            run.status = "quit"
        record("STAGE_INTERRUPTED", "Ctrl-C. Unfinished cash wager released; no extra life consumed.")
    defeat_reason = run.end_reason or ("Boss match lost." if run.encounter_index == len(ENCOUNTERS) - 1
                                      else "Lost with no extra lives remaining.")
    messages = {"victory": "RUN VICTORY! Boss defeated.",
                "defeat": "RUN DEFEAT! " + defeat_reason,
                "quit": "RUN QUIT. Unbanked points were not saved."}
    run.score_history.append(dict(event="RUN_FINISHED",hp=run.hp,target=run.target,status=run.status))
    run.score_summary = calculate_run_score(run.score_history)
    record("RUN_SCORE", "Score: "+json.dumps(run.score_summary,ensure_ascii=False)+
           "\nScoring history: "+json.dumps(run.score_history,ensure_ascii=False))
    record("RUN_END", messages[run.status])
    show_run_summary(run, messages[run.status], output_func)
    return run
