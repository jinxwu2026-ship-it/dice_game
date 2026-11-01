"""Mouse/keyboard interface. Controllers supply state and legal choices."""

from queue import Empty
from math import sin, cos, pi
from pathlib import Path
from time import monotonic

import pygame

from the_kings_gambit.dice import PRICES, face_distribution, die_weights
from the_kings_gambit.gui_session import GameSession
from the_kings_gambit.main import load_leaderboard
from the_kings_gambit.models import Die, DIE_KINDS, QUALITIES
from the_kings_gambit.ui import die_effect_text, ENCOUNTER_STORIES
from the_kings_gambit.scoring import scoring_examples

WIDTH, HEIGHT = 1280, 800
DIE_SIZE = 52
BG = (30, 33, 36)
TEXT = (234, 236, 237)
MUTED = (157, 164, 168)
LINE = (83, 91, 96)
ACCENT = (135, 200, 193)
IVORY = (239, 237, 225)
INK = (30, 34, 37)
ROLL_SECONDS = 0.65
SPIN_SECONDS = 2.2
SPINNER_LABELS = dict(gain_die="Special die",gain_coins="+200 coins",lose_die="Lose die",
                      lose_coins="-150 max",lose_life="Lose ward",nothing="No effect")
DIE_BODY = {"basic": IVORY, "lucky": (174, 202, 188), "two": (164, 195, 181),
            "odd": (184, 207, 192), "even": (166, 195, 189),
            "devil": (139, 176, 167), "angel": (204, 224, 211),
            "momentum": (192, 173, 207), "rescue": (182, 194, 207)}
QUALITY_RIM = {"basic": LINE, "bronze": (192, 130, 69),
               "silver": (214, 223, 232), "gold": (238, 191, 65)}
INTRO_ART = Path(__file__).resolve().parent.parent / "assets" / "gui" / "dragon_wager_intro.png"


def row_rects(area, count, *, width, height, gap=20):
    """Center a row inside its parent region, keeping controls close together."""
    area = pygame.Rect(area)
    left = area.centerx - (count*width + max(0, count-1)*gap)//2
    return [pygame.Rect(left+i*(width+gap), area.centery-height//2, width, height)
            for i in range(count)]


def selection_action(view, slots):
    """Look up a controller-supplied action; the window never scores dice."""
    state = view["state"]
    positions = tuple(i+1 for i, slot in enumerate(state.available_slots) if slot+1 in slots)
    return next((a for a in view["actions"] if tuple(a["selected_positions"]) == positions), None)


def battle_dice(view, selected):
    """Separate physical slots into left tray and center, without duplicating."""
    state = view["state"]
    if view.get("rolling"):
        return sorted(state.held_faces.items()), list(zip(state.available_slots, view["roll"]))
    faces = dict(zip(state.roll_slots, view["roll"]))
    held = dict(state.hot_dice_faces or state.held_faces)
    if state.phase == "select":
        for slot in selected:
            held[slot-1] = faces[slot-1]
        center = [slot for slot in state.available_slots if slot not in held]
    elif state.phase == "decision":
        center = [slot for slot in state.available_slots if slot not in held]
        faces = {}
    else:
        if not held and view["selected_positions"]:
            held = dict(faces)
        center = [slot for slot in state.roll_slots if slot not in held]
    return sorted(held.items()), [(slot, faces.get(slot, "?")) for slot in center]


class GameWindow:
    def __init__(self, *, ai_delay=2, score_ambition=500, time_func=monotonic):
        pygame.display.init()
        pygame.font.init()
        self.window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("The King's Gambit")
        self.surface = pygame.Surface((WIDTH, HEIGHT))
        self.fonts = {}
        self.clock = pygame.time.Clock()
        self.ai_delay, self.score_ambition = ai_delay, score_ambition
        self.session = None
        self.view = dict(screen="menu")
        self.token = None
        self.waiting = self.finished = False
        self.closing = self.returning = False
        self.selected = set()
        self.choice = {}
        self.buttons = []
        self.hover = None
        self.mouse = (-1, -1)
        self.basic = tuple(Die() for _ in range(6))
        self.guide_dice = {kind: Die(kind,"silver" if kind in ("devil","angel","rescue") else "bronze")
                           for kind in DIE_KINDS if kind != "basic"}
        self.guide_qualities = {quality: Die("lucky",quality) for quality in QUALITIES}
        self.log_path = None
        self.overlays = []
        self.focus = None
        self.focus_context = None
        self.die_details = []
        self.now = time_func
        self.roll_started = None
        self.intro_art = None
        self.auto_next = None
        self.rule_examples = scoring_examples()

    def regions(self):
        """HUD corners and play areas share an inset reference canvas."""
        safe = self.surface.get_rect().inflate(-72, -72)
        body = pygame.Rect(safe.left, safe.top+164, safe.width, safe.height-278)
        return dict(safe=safe, scores=pygame.Rect(safe.left, safe.top, 280, 120),
                    risk=pygame.Rect(safe.right-280, safe.top+8, 280, 120),
                    tray=pygame.Rect(body.left, body.top, 290, body.height),
                    pool=pygame.Rect(body.left+330, body.top, 588, body.height),
                    recent=pygame.Rect(body.right-220, body.top, 220, body.height),
                    actions=pygame.Rect(safe.right-710, safe.bottom-84, 680, 68))

    def font(self, size=22, bold=False):
        key = size, bold
        if key not in self.fonts:
            self.fonts[key] = pygame.font.SysFont("segoeui", size, bold=bold)
        return self.fonts[key]

    def text(self, value, x, y, size=22, color=TEXT, center=False, bold=False):
        rendered = self.font(size, bold).render(str(value), True, color)
        rect = rendered.get_rect(midtop=(x, y)) if center else rendered.get_rect(topleft=(x, y))
        self.surface.blit(rendered, rect)
        return rect

    def lines(self, value, x, y, width, size=19, color=MUTED):
        """Wrap descriptions inside their region instead of clipping text."""
        for paragraph in str(value).splitlines():
            line = ""
            for word in paragraph.split():
                trial = (line + " " + word).strip()
                if line and self.font(size).size(trial)[0] > width:
                    self.text(line, x, y, size, color)
                    y += size + 7
                    line = word
                else:
                    line = trial
            self.text(line, x, y, size, color)
            y += size + 7
        return y

    def rule(self, x1, y1, x2, y2):
        pygame.draw.line(self.surface, LINE, (x1, y1), (x2, y2))

    def button(self, label, rect, action, *, enabled=True, active=False, primary=False):
        rect = pygame.Rect(rect)
        hover = rect.collidepoint(self.mouse) and enabled
        color = ACCENT if enabled and (hover or active) else LINE
        fill = ACCENT if primary and enabled else (43, 48, 51) if hover or active else BG
        pygame.draw.rect(self.surface, fill, rect, border_radius=5)
        pygame.draw.rect(self.surface, color, rect, width=1, border_radius=5)
        self.text(label, rect.centerx, rect.y + (rect.h-25)//2, 20,
                  INK if primary and enabled else TEXT if enabled else LINE, center=True, bold=True)
        if enabled:
            self.buttons.append((rect, action))

    def icon(self, kind, x, y, size=9, color=INK, surface=None):
        surface = self.surface if surface is None else surface
        if kind == "basic":
            return
        if kind == "momentum":
            pygame.draw.lines(surface,color,False,[(x-size,y+size//2),(x,y-size),(x+size,y+size//2)],2)
        elif kind == "rescue":
            pygame.draw.arc(surface,color,(x-size,y-size,size*2,size*2),.2,5.1,2)
            pygame.draw.polygon(surface,color,[(x+size,y-size),(x+size,y+2),(x-1,y-size)])
        elif kind == "two":
            pygame.draw.polygon(surface, color, [(x,y-size),(x+size,y),(x,y+size),(x-size,y)])
        elif kind in ("odd", "devil"):
            pygame.draw.polygon(surface, color, [(x,y-size),(x+size,y+size//2),(x-size,y+size//2)])
            if kind == "devil":
                pygame.draw.circle(surface, color, (x-size//2,y+size//3), max(2,size//2))
                pygame.draw.circle(surface, color, (x+size//2,y+size//3), max(2,size//2))
                pygame.draw.line(surface, color, (x,y), (x,y+size), 2)
        elif kind == "even":
            pygame.draw.rect(surface, color, (x-size*.75,y-size*.75,size*1.5,size*1.5))
        elif kind in ("lucky", "angel"):
            for dx in (-size//2, size//2):
                pygame.draw.circle(surface, color, (x+dx,y-size//3), max(2,size//2))
            if kind == "lucky":
                pygame.draw.circle(surface, color, (x,y-size), max(2,size//2))
                pygame.draw.line(surface, color, (x,y), (x,y+size), 3)
            else:
                pygame.draw.polygon(surface, color, [(x-size,y),(x+size,y),(x,y+size)])

    def die_face(self, die, face, size=DIE_SIZE):
        """A reusable face sprite: family body, inset type and metal quality band."""
        sprite = pygame.Surface((size,size), pygame.SRCALPHA)
        body, rim = DIE_BODY[die.kind], QUALITY_RIM[die.quality]
        special = die.kind != "basic"
        pygame.draw.rect(sprite, body, sprite.get_rect(), border_radius=6)
        pygame.draw.rect(sprite, rim, sprite.get_rect(), width=3 if special else 1, border_radius=6)
        if special:
            band = pygame.Rect(3,size-13,size-6,10)
            pygame.draw.rect(sprite, rim, band, border_radius=2)
            for i in range(("bronze","silver","gold").index(die.quality)+1):
                pygame.draw.rect(sprite, INK, (8+i*8,size-11,3,6))
            letter = self.font(11,True).render(die.quality[0].upper(),True,INK)
            sprite.blit(letter, (size-14,size-15))
            self.icon(die.kind,8,8,4,INK,sprite)
        cx, cy = size//2, round(size*.4) if special else size//2
        if face == 0:
            # The wildcard face is a head, rather than a natural 1 or 5.
            if die.kind == "devil":
                pygame.draw.circle(sprite,INK,(cx,cy+2),9)
                for direction in (-1,1):
                    pygame.draw.polygon(sprite,INK,[(cx+direction*9,cy),
                                                   (cx+direction*11,cy-12),(cx+direction*2,cy-4)])
                for dx in (-4,4):
                    pygame.draw.circle(sprite,body,(cx+dx,cy+1),2)
            else:
                pygame.draw.circle(sprite,INK,(cx,cy+3),7)
                pygame.draw.ellipse(sprite,INK,(cx-10,cy-12,20,6),2)
                for direction in (-1,1):
                    pygame.draw.polygon(sprite,INK,[(cx+direction*5,cy+8),
                                                   (cx+direction*14,cy),(cx+direction*13,cy+12)])
        elif face == "?":
            glyph = self.font(27,True).render("?",True,INK)
            sprite.blit(glyph,glyph.get_rect(center=(cx,cy)))
        else:
            spots = {1: [(1,1)], 2: [(0,0),(2,2)], 3: [(0,0),(1,1),(2,2)],
                     4: [(0,0),(2,0),(0,2),(2,2)],
                     5: [(0,0),(2,0),(1,1),(0,2),(2,2)],
                     6: [(0,0),(2,0),(0,1),(2,1),(0,2),(2,2)]}
            for dx, dy in spots.get(face, []):
                point = (round(size*(.32+dx*.2)),round(size*(.22+dy*.2))) if special else (
                         round(size*(.25+dx*.25)),round(size*(.25+dy*.25)))
                pygame.draw.circle(sprite,INK,point,max(2,round(size*.06)))
        return sprite

    def die(self, die, face, x, y, *, slot=None, selected=False, action=None, size=DIE_SIZE, rolling=False):
        rect = pygame.Rect(x, y, size, size)
        elapsed = max(0,self.now()-self.roll_started) if rolling and self.roll_started is not None else ROLL_SECONDS
        progress = min(1,elapsed/ROLL_SECONDS)
        if rolling and progress < .85:
            # Decorative cycling is deterministic and never consumes game randomness.
            values = (0,2,3,4,5,6) if die.kind == "devil" else (1,2,3,4,0,6) if die.kind == "angel" else (1,2,3,4,5,6)
            face = values[(int(elapsed*22)+(slot or 0)) % 6]
        sprite = self.die_face(die,face,size)
        if rolling:
            wave = sin(progress*pi*5+(slot or 0)*.7)*(1-progress)
            sprite = pygame.transform.rotate(sprite,wave*18)
            pos = (rect.centerx+wave*8,rect.centery-abs(wave)*16)
        else:
            pos = rect.center
        self.surface.blit(sprite,sprite.get_rect(center=pos))
        if selected:
            pygame.draw.rect(self.surface,ACCENT,rect.inflate(6,6),width=1,border_radius=7)
            badge = (rect.right-1, rect.top+1)
            pygame.draw.circle(self.surface, ACCENT, badge, 8)
            pygame.draw.lines(self.surface, INK, False,
                              [(badge[0]-4,badge[1]),(badge[0]-1,badge[1]+3),
                               (badge[0]+4,badge[1]-3)], 2)
        if slot is not None:
            self.text(slot, rect.centerx, y+size+5, 15, MUTED, center=True)
        if rect.collidepoint(self.mouse):
            self.hover = die
        if action is not None:
            self.buttons.append((rect.inflate(8,8), action))
            self.die_details.append((action, die))

    def emblem(self, label, dragon=False):
        x, y = self.surface.get_rect().centerx, self.regions()["safe"].top+28
        if dragon:
            pygame.draw.polygon(self.surface,ACCENT,[(x-26,y+12),(x-14,y-13),(x-7,y-29),
                (x+1,y-8),(x+16,y-23),(x+15,y-3),(x+32,y+13),(x+12,y+23),(x-8,y+32)],2)
            pygame.draw.circle(self.surface,TEXT,(x+9,y+6),3)
        else:
            pygame.draw.lines(self.surface, MUTED, False,
                          [(x-26,y+33),(x-29,y+14),(x-18,y-10),(x,y-27),
                           (x+18,y-10),(x+29,y+14),(x+26,y+33)], 2)
            pygame.draw.polygon(self.surface, TEXT, [(x-12,y+2),(x+12,y+2),(x,y+20)])
        self.text(label, x, 111, 17, MUTED, center=True)

    def header(self, title, *, opponent=False, scores=None, target=2000):
        areas = self.regions()
        safe, score_area = areas["safe"], areas["scores"]
        if opponent:
            self.emblem(title,self.view.get("resources",{}).get("stage") == 5)
        else:
            self.text(title, 640, 55, 29, center=True, bold=True)
        if scores is not None:
            for i, (side, label) in enumerate((("Player", "YOU"), ("Opponent", "AI"))):
                if side not in scores:
                    continue
                x, y = score_area.x+4, score_area.y+6+i*57
                points = scores.get(side, 0)
                self.text(f"{label}   {points} / {target}", x, y, 18)
                pygame.draw.rect(self.surface, LINE, (x,y+30,270,9), width=1)
                pygame.draw.rect(self.surface, ACCENT, (x+1,y+31,round(268*min(points/target,1)),7))
        self.rule(safe.left, safe.top+131, safe.right, safe.top+131)
        self.rule(safe.left, safe.bottom-114, safe.right, safe.bottom-114)
        running = self.session is not None and not self.finished
        if self.view["screen"] not in ("run_score","leaderboard"):
            self.button("Exit run" if running else "Menu", (safe.right-128,10,128,34), "menu")
            self.button("Rules",(safe.right-244,10,96,34),"rules")
        resources = self.view.get("resources", {})
        if resources.get("hp") is not None:
            self.text(f"WARD {resources['hp']}", 40, 680, 24, bold=True)
            self.text("extra lives", 40, 715, 15, MUTED)
            self.rule(166,678,166,736)
            self.text(f"COINS {resources['coins']}", 192, 680, 24, bold=True)

    def start(self, mode):
        self.session = GameSession(mode, ai_delay=self.ai_delay, score_ambition=self.score_ambition)
        self.waiting = self.finished = False
        self.token = None
        self.log_path = None
        self.selected.clear()
        self.choice.clear()
        self.roll_started = None
        self.auto_next = None
        self.view = dict(screen="loading")
        self.session.start()

    def poll(self):
        if self.session is None:
            return
        if self.auto_next and not self.overlays:
            token, deadline = self.auto_next
            if token != self.token or not self.waiting:
                self.auto_next = None
            elif self.now() >= deadline:
                self.send("")
        if self.roll_started is not None:
            duration = SPIN_SECONDS if self.view["screen"] == "spinner_roll" else ROLL_SECONDS
            if self.now()-self.roll_started < duration:
                return
            self.roll_started = None
        while True:
            try:
                event = self.session.bridge.events.get_nowait()
            except Empty:
                break
            if event["kind"] in ("view", "input"):
                self.auto_next = None
                self.view = event["view"] or dict(screen="loading")
                self.waiting = event["kind"] == "input"
                self.token = event.get("token")
                if self.view["screen"] in ("guess_roll","spinner_roll"):
                    if self.returning or self.closing:
                        continue
                    self.waiting,self.token = False,None
                    self.selected.clear()
                    self.roll_started = self.now()
                    break
                if self.view["screen"] == "rolling":
                    if self.returning or self.closing:
                        continue
                    self.view = dict(self.view,screen="battle",rolling=True)
                    self.waiting, self.token = False, None
                    self.selected.clear()
                    self.roll_started = self.now()
                    break  # Keep queued decisions behind this roll's presentation.
                if self.waiting:
                    self.selected.clear()
                    self.choice = {}
                    self.schedule_turn_end()
            elif event["kind"] == "finished":
                self.finished, self.waiting, self.token = True, False, None
                self.log_path = event["log_path"]
                if self.session.mode != "run":
                    result = event["result"]
                    self.view = dict(screen="complete", result=result)
            elif event["kind"] == "error":
                self.finished, self.waiting, self.token = True, False, None
                self.view = dict(screen="error", message=event["message"])
        if self.returning and self.finished:
            self.returning = False
            self.session.thread.join()
            self.session = None
            self.view = dict(screen="menu")

    def send(self, command):
        if self.roll_started is None and self.session and self.waiting and self.session.bridge.submit(self.token, command):
            self.waiting = False
            self.token = None
            self.auto_next = None

    def schedule_turn_end(self):
        state = self.view.get("state")
        if self.waiting and state is not None and state.phase == "ended" and state.outcome in ("bust","bank"):
            self.auto_next = (self.token,self.now()+1.0)

    def dismiss_overlay(self):
        self.focus = self.overlays.pop()["focus"]
        if not self.overlays:
            self.schedule_turn_end()

    def activate(self, action):
        if self.returning or self.closing:
            return
        if self.overlays:
            if self.overlays[-1]["kind"] == "rules":
                if action == "close_rules":
                    self.dismiss_overlay()
                elif isinstance(action,tuple) and action[0] == "rules_page":
                    self.overlays[-1]["page"] = action[1]
                elif action == "exit":
                    self.overlays.append(dict(kind="exit",destination="exit",focus=self.focus))
                    self.focus = "keep_playing"
            elif action == "keep_playing":
                self.dismiss_overlay()
            elif action == "end_game":
                self.end_game(self.overlays.pop()["destination"])
            return
        if action == "menu":
            if self.session and not self.finished:
                self.overlays.append(dict(kind="exit",destination="menu", focus=self.focus))
                self.focus = "keep_playing"
            else:
                self.session = None
                self.view = dict(screen="menu")
            return
        if action == "new_run":
            self.start("run")
        elif action == "rules":
            if self.view["screen"] == "menu":
                self.view = dict(screen="rules",page=0)
            else:
                self.overlays.append(dict(kind="rules",page=0,focus=self.focus))
                self.focus = ("rules_page",0)
        elif action == "leaderboard":
            self.view = dict(screen="leaderboard",entries=load_leaderboard(),page=0)
        elif action == "exit":
            if self.session and not self.finished:
                self.overlays.append(dict(kind="exit",destination="exit", focus=self.focus))
                self.focus = "keep_playing"
            else:
                self.end_game("exit")
        elif action == "clear_selection":
            self.selected.clear()
        elif action == "skip_roll":
            self.roll_started = None
        elif isinstance(action, tuple):
            kind, value = action
            if kind == "select":
                if value in self.selected:
                    self.selected.remove(value)
                else:
                    self.selected.add(value)
            elif kind == "choice":
                key, value = value
                self.choice[key] = value
                if key == "mode":
                    self.selected.clear()
            elif kind == "send":
                self.send(value)
            elif kind == "page":
                self.view["page"] = value
            elif kind == "rules_page":
                self.view["page"] = value

    def end_game(self, destination):
        """Cancellation still belongs to the controller, including refunds/logs."""
        self.closing = destination == "exit"
        self.returning = destination == "menu"
        self.roll_started = None
        self.auto_next = None
        if self.session:
            self.session.close()

    def exit_dialog(self):
        shade = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 175))
        self.surface.blit(shade, (0,0))
        panel = pygame.Rect(0,0,600,310)
        panel.center = self.surface.get_rect().center
        pygame.draw.rect(self.surface, BG, panel, border_radius=8)
        pygame.draw.rect(self.surface, LINE, panel, width=1, border_radius=8)
        self.text("End this run?", panel.centerx, panel.top+28, 30, center=True, bold=True)
        self.text("Progress is not saved.", panel.centerx, panel.top+89, 21, center=True)
        self.text("Unfinished wagers are returned.", panel.centerx, panel.top+122, 21, center=True)
        self.text("AI turns continue while this dialog is open.", panel.centerx,
                  panel.top+164, 17, MUTED, center=True)
        # Only the top overlay registers controls; the board stays live underneath.
        self.buttons, self.die_details, self.hover = [], [], None
        area = pygame.Rect(panel.left+24, panel.bottom-84, panel.width-48, 60)
        for rect, label, action in zip(row_rects(area, 2, width=240, height=48),
                                       ("Keep playing", "End run"),
                                       ("keep_playing", "end_game")):
            self.button(label, rect, action, primary=action == "keep_playing")

    def inventory(self, dice, *, allowed=None, y=479):
        area = pygame.Rect(390, y, 480, DIE_SIZE)
        for i, (die, rect) in enumerate(zip(dice, row_rects(area, len(dice), width=DIE_SIZE,
                                                          height=DIE_SIZE, gap=24)), 1):
            self.die(die, "?", rect.x, rect.y, slot=i, selected=i in self.selected,
                     action=("select",i) if self.waiting and (allowed is None or i in allowed) else None)

    def merge_controls(self, merges):
        mode = self.choice.get("mode")
        self.button("Merge Dice", (1030,450,185,42), ("choice",("mode","merge")),
                    enabled=self.waiting and bool(merges), active=mode == "merge")
        if mode == "merge":
            self.inventory(self.view["run"].dice, y=549)
            pair = tuple(sorted(self.selected))
            self.button("Confirm Merge", (1030,504,185,42), ("send","m " + " ".join(map(str,pair))),
                        enabled=self.waiting and pair in merges)

    def battle(self):
        v, state = self.view, self.view["state"]
        phase = "rolling" if v.get("rolling") else state.phase
        scores = dict(v["match_scores"] or {})
        scores[v["active_side"]] = state.match_score
        label = v["ai_label"].replace("Normal (", "").replace(")", "").upper()
        stage = v["resources"].get("stage")
        title = f"BATTLE {stage} · {ENCOUNTER_STORIES[stage-1][0].upper()}" if stage else (label if v["match_scores"] else "PRACTICE")
        self.header(title, opponent=bool(v["match_scores"]), scores=scores, target=state.target)
        action = selection_action(v, self.selected) if phase == "select" else None
        areas = self.regions()
        tray, pool, recent, risk = (areas[key] for key in ("tray", "pool", "recent", "risk"))
        self.text(f"TURN {v['turn_number']}", risk.x, risk.y, 17, MUTED)
        self.text("AT RISK", risk.x, risk.y+44, 18)
        self.text(state.unbanked_score, risk.x+105, risk.y+27, 42, bold=True)
        if action:
            self.text(f"+{action['score_delta']} selected  →  {state.unbanked_score+action['score_delta']}",
                      risk.x, risk.y+88, 20, ACCENT, bold=True)
        elif phase == "decision":
            self.text(f"+{v.get('selection_score', 0)} confirmed", risk.x, risk.y+88, 20, MUTED)
        self.rule(tray.right+20, tray.top+30, tray.right+20, tray.bottom-20)
        self.rule(recent.left-20, recent.top+30, recent.left-20, recent.bottom-20)
        self.text("YOUR TURN" if v["active_side"] == "Player" else "AI TURN",
                  pool.centerx, pool.top+5, 30, center=True, bold=True)
        stage_text = {"select":"Select scoring dice", "decision":"Roll again or bank your points",
                      "rescue":"No scoring dice · Rescue or accept Bust?",
                      "ended":"Turn complete"}.get(phase, "Rolling dice...")
        self.text(stage_text, pool.centerx, pool.top+50, 20, MUTED, center=True)
        held, center = battle_dice(v, self.selected)
        self.text(f"SELECTED · {len(held)}", tray.x+24, tray.top+45, 18, MUTED, bold=True)
        self.text(f"REMAINING DICE · {state.dice_available if phase == 'decision' else len(center)}",
                  pool.centerx, pool.top+112, 18, MUTED, center=True, bold=True)
        dice = state.dice or self.basic
        can_select = self.waiting and phase == "select" and v["active_side"] == "Player"
        for i, (slot, face) in enumerate(held):
            cells = row_rects((tray.x, tray.top+145+(i//3)*100, tray.width, DIE_SIZE),
                              3, width=DIE_SIZE, height=DIE_SIZE, gap=28)
            rect = cells[i%3]
            self.die(dice[slot], face, rect.x, rect.y, slot=slot+1, selected=True,
                     action=("select",slot+1) if can_select and slot+1 in self.selected else None)
        cells = row_rects((pool.x, pool.top+175, pool.width, DIE_SIZE), len(center),
                          width=DIE_SIZE, height=DIE_SIZE, gap=24)
        for (slot, face), rect in zip(center, cells):
            self.die(dice[slot], face, rect.x, rect.y, slot=slot+1,
                     action=("select",slot+1) if can_select else None, rolling=phase == "rolling")
        if action:
            self.text(f"Preview  +{action['score_delta']}", tray.centerx, tray.bottom-60,
                      24, ACCENT, center=True, bold=True)
        elif phase == "select" and v["active_side"] == "Player":
            self.text("Click dice to move here", tray.centerx, tray.bottom-60, 17, MUTED, center=True)
        self.text("RECENT ACTION", recent.x, recent.top+45, 17, MUTED)
        if v["active_side"] == "Opponent":
            self.lines(v.get("dialogue") or "Let's see what the dice bring.",recent.x,recent.top+80,recent.width,21,TEXT)
            self.lines(v.get("action_fact", ""),recent.x,recent.top+210,recent.width,17,MUTED)
        else:
            self.lines(v["message"], recent.x, recent.top+80, recent.width, 18, TEXT)
        status = []
        if any(d.kind == "momentum" for d in dice):
            status.append(f"Momentum {state.successes} successes")
        if any(d.kind == "rescue" for d in dice):
            status.append(f"Rescue {state.ability_budget['rescue']}/1")
        if status:
            self.text(" · ".join(status),pool.x+20,pool.bottom-175,18,MUTED)
        if action and "bonus_score" in action:
            self.text(f"Base {action['base_score']} + Momentum {action['bonus_score']}",
                      pool.x+20,pool.bottom-145,18,ACCENT)
        if can_select and state.can_rescue:
            self.button("Use rescue · 1 left",(pool.right-260,pool.bottom-135,240,40),("send","r"))
        if phase == "select" and self.selected and not action:
            self.lines("Invalid selection: use scoring singles or a complete combination.",
                       pool.x+20, pool.bottom-85, pool.width-40)
        if action and action.get("wild_values"):
            mapping = {state.available_slots[i-1]+1: n for i,n in action["wild_values"].items()}
            self.text(f"Wildcard use: {mapping}", pool.x+20, pool.bottom-85, 18, ACCENT)
        elif state.last_mapping and phase != "rolling":
            self.text(f"Wildcard use: {state.last_mapping}", pool.x+20, pool.bottom-85, 18, ACCENT)
        self.lines(v["first_turn"], pool.x+20, areas["safe"].bottom-158, pool.width-40, 16)
        controls = row_rects(areas["actions"], 2, width=270, height=48)
        if phase == "rolling":
            self.button("Skip animation",controls[1],"skip_roll")
        elif v["active_side"] == "Opponent" and phase != "ended":
            self.text("Watching AI decisions...", areas["actions"].centerx,
                      areas["actions"].y+20, 22, MUTED, center=True)
        elif phase == "ended":
            result = f"BUST · Lost {state.lost_score}" if state.outcome == "bust" else f"BANK · Saved {state.banked_points}"
            self.text(f"{result} · Next turn automatically",
                      areas["actions"].centerx,areas["actions"].y+20,20,ACCENT,center=True)
        elif phase == "rescue":
            self.button("Use rescue · 1 left",controls[0],("send","r"),enabled=self.waiting,primary=True)
            self.button("Accept Bust",controls[1],("send","s"),enabled=self.waiting)
        elif phase == "select":
            # Basic CLI turns take roll-relative positions; equipped turns take fixed slots.
            positions = action["selected_positions"] if action and state.dice is None else sorted(self.selected)
            command = " ".join(map(str, positions))
            confirm = ("Reroll Six (+0)" if action and action["action_type"] == "ordinary_pairs"
                       else f"Confirm +{action['score_delta']}" if action else "Confirm selection")
            self.button(confirm, controls[0], ("send",command), enabled=can_select and action is not None,
                        primary=True)
            self.button("Clear selection", controls[1], "clear_selection", enabled=can_select and bool(self.selected))
            self.text("1  SELECT", pool.x, areas["actions"].y+5, 17, ACCENT, bold=True)
            self.text("2  ROLL / BANK", pool.x, areas["actions"].y+34, 17, MUTED)
        elif phase == "decision":
            decision = self.waiting and v["active_side"] == "Player"
            self.button(f"Roll {state.dice_available}", controls[0], ("send","r"), enabled=decision)
            self.button(f"Bank {state.unbanked_score}", controls[1], ("send","b"), enabled=decision)
            self.text("2  ROLL / BANK", pool.x, areas["actions"].y+20, 17, ACCENT, bold=True)
            self.text(f"Risk {state.unbanked_score}", controls[0].centerx, controls[0].bottom+8, 17, MUTED, center=True)
            self.text(f"Banked total → {state.match_score+state.unbanked_score}",
                      controls[1].centerx, controls[1].bottom+8, 17, MUTED, center=True)
            if not center:
                self.text("HOT DICE · All six can roll again", pool.centerx, pool.bottom-85,
                          21, ACCENT, center=True)

    def growth(self):
        v, screen = self.view, self.view["screen"]
        run = v["run"]
        title = {"initial":"THE DRAGON'S WAGER", "wager":"WAGER", "reward":"RECEIVE DIE",
                 "guess_intro":"GUESS SIZE", "guess":"GUESS SIZE", "guess_claim":"GUESS SIZE",
                 "spinner":"SPINNER", "shop":"SHOP", "run_summary":"RUN SUMMARY"}[screen]
        if screen == "wager":
            self.header(v["encounter"]["ai_type"].upper(), opponent=True,
                        scores={"Player":0,"Opponent":0}, target=run.target)
        else:
            last_scores = run.history[-1]["scores"] if run.history else None
            self.header(title, scores=last_scores, target=run.target)
        if screen != "initial":
            self.lines(v.get("story", ""),60,185,1150,18,ACCENT)
        active = self.waiting
        if screen == "initial":
            self.opening()
            self.button("Draw 3 starting dice", (720,680,270,48), ("send","p"), enabled=active, primary=True)
            self.button("Skip draw", (1010,680,200,48), ("send","s"), enabled=active)
        elif screen == "wager":
            self.text(f"BATTLE {v['stage']}", 1000, 64, 20)
            self.text(f"MAX BET {v['cap']}", 1000, 104, 20)
            mode_y = 240
            if v["stage"] == 5:
                bounty = self.text("Victory bounty: at least one Gold die",640,225,20,ACCENT,center=True)
                mode_y = bounty.bottom+14
            self.die(v["main"], "?", 180, 300)
            self.lines(f"AI stake: {v['main'].kind.title()} · {v['main'].quality.title()}", 65, 395, 260)
            mode = self.choice.get("mode","cash")
            for i, (text, value) in enumerate((("Coins","cash"),("Die","die"))):
                self.button(text, (450+i*205,mode_y,190,44), ("choice",("mode",value)),
                            enabled=active and (value == "cash" or bool(v["choices"])), active=mode == value)
            if mode == "cash":
                amount = self.choice.get("amount",0)
                for i, number in enumerate(v["cash_amounts"]):
                    self.button(str(number), (400+i*85,330,74,45), ("choice",("amount",number)), enabled=active, active=amount == number)
                self.text(f"Win: +{amount} wager +{v['bonus']} bonus", 430, 420, 21)
                self.text(f"Lose: -{amount} coins", 430, 459, 20, MUTED)
                command, valid = f"c {amount}", True
            elif mode == "die":
                self.inventory(run.dice, allowed=v["choices"], y=350)
                slot = next(iter(self.selected)) if len(self.selected) == 1 else None
                valid = slot in v["choices"]
                command = f"d {slot}"
                if valid:
                    prize = v["choices"][slot]
                    self.lines(f"Win: keep your die and receive {prize.kind.title()} {prize.quality.title()} + {v['bonus']} coins. Lose: your staked die.", 400, 470, 570)
                else:
                    self.text("Choose one matching-quality die.", 410, 470, 20, MUTED)
            else:
                command, valid = "", False
            self.merge_controls(v["merges"])
            self.button("Confirm Wager", (920,680,290,48), ("send",command), enabled=active and valid)
            self.lines(v["message"], 400, 594, 790, 16)
        elif screen == "reward":
            self.die(v["die"], "?", 614, 265)
            self.text(f"{v['die'].kind.title()} · {v['die'].quality.title()}", 640, 350, 24, center=True)
            self.text(f"{v['source'].title()} reward" + (f" · Cost {v['cost']}" if v['cost'] else ""), 640, 395, 19, MUTED, center=True)
            if v.get("batch"):
                self.text(f"Starting die {v['batch'][0]} / {v['batch'][1]}",1000,90,20,MUTED)
            allowed = v.get("placement_slots",range(1,7))
            self.inventory(v["planned"],allowed=set(allowed)|set(v["merge_slots"]), y=480)
            slot = next(iter(self.selected)) if len(self.selected) == 1 else None
            self.text("Choose the slot to replace, or preview a matching merge.", 640, 570, 18, MUTED, center=True)
            self.lines(v["message"], 400, 605, 800, 16)
            self.button(f"Keep in Slot {slot or '-'}", (470,680,230,48), ("send",str(slot)), enabled=active and slot in allowed)
            self.button("Preview Merge", (720,680,230,48), ("send",f"m {slot}"), enabled=active and slot in v["merge_slots"])
            decline = f"Decline (+{v['cashout']})" if v["cashout"] else "Cancel" if v["source"] == "shop" else "Decline"
            self.button(decline, (970,680,240,48), ("send","d"), enabled=active)
        elif screen.startswith("guess"):
            if screen == "guess_intro":
                self.lines("Up to three guesses. First win: a Silver die. Next wins: +100, then +200 coins. Claim after a win or risk pending prizes. A miss does not take existing assets.", 380, 285, 550, 23)
                buttons = (("Start Event","p"),("Skip","s"))
            else:
                self.text(f"ATTEMPT {v['attempt']} / 3", 1000, 75, 21)
                self.die(v.get("die",v.get("prize")), v.get("face","?"), 614, 255)
                if screen == "guess":
                    self.text(f"Prize: {v['prize'].kind.title()} · Silver", 640, 355, 23, center=True)
                    self.text(f"Small: {v['small']:.1%}     Big: {1-v['small']:.1%}", 640, 415, 23, center=True)
                    buttons = (("Small 1-3","s"),("Big 4-6","b"))
                else:
                    self.text("Correct!", 640, 365, 27, ACCENT, center=True)
                    buttons = (("Claim Prizes","b"),("Continue Guessing","r"))
                self.text(f"Pending coins: {v['pending_coins']}", 640, 490, 22, center=True)
                self.text("A miss loses all pending prizes.", 640, 540, 19, MUTED, center=True)
            for i,(label, command) in enumerate(buttons):
                self.button(label, (700+i*260,680,245,48), ("send",command), enabled=active)
        elif screen == "spinner":
            self.text(f"DRAW {v['attempt']} / 3", 1000, 75, 21)
            total = sum(v["remaining"].values())
            self.wheel(v["remaining"])
            for i,(item,weight) in enumerate(v["remaining"].items()):
                self.text(SPINNER_LABELS[item], 855, 255+i*43, 20)
                self.text(f"{weight/total:.1%}", 1090, 255+i*43, 20, ACCENT)
            self.lines(v["message"], 390, 603, 810,16)
            if run.hp == 0:
                self.text("Losing a life ends this run now.", 855, 540, 18, ACCENT)
            self.button("Spin", (760,680,210,48), ("send","p"), enabled=active)
            self.button("Stop", (990,680,220,48), ("send","s"), enabled=active)
        elif screen == "shop":
            for i, die in enumerate(v["stock"]):
                x,y = 410+(i%3)*190, 240+(i//3)*150
                if die is None:
                    self.text("SOLD", x, y+28, 21, MUTED)
                    continue
                self.die(die, "?", x, y)
                self.text(f"{die.kind.title()} · {die.quality[0].upper()}", x+66, y, 18)
                self.text(PRICES[die.quality], x+66, y+29, 18, MUTED)
                self.button("Buy", (x,y+75,150,34), ("send",f"buy {i+1}"), enabled=active and run.coins >= PRICES[die.quality])
            self.rule(1000,210,1000,620)
            mode = self.choice.get("mode")
            for i,(name,price) in enumerate((("upgrade",300),("remove",50))):
                self.button(f"{name.title()} {price}", (1030,245+i*65,185,44), ("choice",("mode",name)),
                            enabled=active and not v["serviced"] and run.coins >= price and bool(v[name+"_slots"]), active=mode == name)
            self.text("One paid service", 1030, 385, 17, MUTED)
            if mode in ("upgrade","remove"):
                self.inventory(run.dice, allowed=v[mode+"_slots"], y=549)
                slot = next(iter(self.selected)) if len(self.selected) == 1 else None
                self.button("Apply Service", (1030,515,185,42), ("send",f"{mode} {slot}"), enabled=active and slot in v[mode+"_slots"])
            elif mode != "merge":
                self.inventory(run.dice, allowed=(), y=549)
            self.merge_controls(v["merges"])
            self.lines(v["message"], 400, 618, 580, 15)
            self.button("Refresh 200 · once", (690,680,260,48), ("send","refresh"), enabled=active and not v["refreshed"] and run.coins >= 200)
            self.button("Continue to Boss", (970,680,240,48), ("send","leave"), enabled=active)
        elif screen == "run_summary":
            self.text(run.status.upper() if not run.is_active else "BATTLE COMPLETE", 640, 215, 30, center=True, bold=True)
            for i, result in enumerate(run.history):
                scores = result["scores"]
                self.text(f"{result['stage']}  {result['ai_type'].title()}", 380, 290+i*44, 22)
                self.text(f"You {scores['Player']}  /  AI {scores['Opponent']}", 660, 290+i*44, 22)
                self.text("WIN" if result["winner"] == "Player" else "LOSS", 1050, 290+i*44, 20, MUTED)
            self.lines(v["message"], 380, 535, 800, 18)
            if self.finished:
                self.button("Main Menu", (930,680,280,48), "menu")
            else:
                self.button("Continue", (930,680,280,48), ("send",""), enabled=active)

    def wheel(self, weights, chosen=None, progress=None):
        """Visual sectors use supplied weights/result; animation never draws randomness."""
        total = sum(weights.values())
        before = sum(weight for item,weight in list(weights.items())[:list(weights).index(chosen)]) if chosen else 0
        target = 1440-360*(before+weights[chosen]/2)/total if chosen else 0
        angle = target*(1-(1-progress)**3) if progress is not None else target
        cx,cy,radius = 600,403,170
        start = 0
        for i,(item,weight) in enumerate(weights.items()):
            end = start+2*pi*weight/total
            rotation = angle*pi/180-pi/2
            steps = max(3,round(80*weight/total))
            points = [(cx,cy)]+[(cx+radius*cos(start+(end-start)*j/steps+rotation),
                                cy+radius*sin(start+(end-start)*j/steps+rotation)) for j in range(steps+1)]
            color = (66,91,89) if item == chosen and progress is None else ((48,54,58) if i%2 else (58,65,69))
            pygame.draw.polygon(self.surface,color,points)
            pygame.draw.lines(self.surface,LINE,True,points,1)
            mid = (start+end)/2+rotation
            self.text(SPINNER_LABELS[item],cx+105*cos(mid),cy+105*sin(mid)-8,15,TEXT,center=True)
            start = end
        pygame.draw.circle(self.surface,LINE,(cx,cy),radius,2)
        pygame.draw.polygon(self.surface,ACCENT,[(cx-11,cy-radius-20),(cx+11,cy-radius-20),(cx,cy-radius+2)])

    def event_view(self):
        v = self.view
        spinning = v["screen"] == "spinner_roll"
        rolling = v["screen"] in ("guess_roll","spinner_roll")
        is_spinner = spinning or v.get("event_type") == "spinner"
        self.header("WHEEL OF FORTUNE" if is_spinner else "GUESS SIZE")
        self.text(f"ATTEMPT {v['attempt']} / 3",1000,100,19,MUTED)
        if is_spinner:
            elapsed = SPIN_SECONDS if self.roll_started is None else self.now()-self.roll_started
            progress = min(1,elapsed/SPIN_SECONDS) if spinning else None
            self.wheel(v["remaining"],v["chosen"],progress)
            self.lines("Spinning..." if spinning else SPINNER_LABELS[v["chosen"]],850,300,330,27,ACCENT)
            if not rolling:
                self.lines(v["message"],850,370,330,20)
        else:
            self.die(v["die"],v["face"],614,320,rolling=rolling)
            self.text("Rolling..." if rolling else ("Correct!" if v["correct"] else "Miss"),640,430,27,ACCENT,center=True)
            if rolling:
                self.text(f"Your guess: {v['guess']}",640,265,23,center=True)
            else:
                self.lines(v["message"],390,495,790,22)
        if rolling:
            self.button("Skip animation",(930,680,280,48),"skip_roll")
        else:
            self.button("Continue",(930,680,280,48),("send",""),enabled=self.waiting)

    def score_screen(self):
        v,run = self.view,self.view["run"]
        score = v["score"]
        self.header("JOURNEY COMPLETE")
        self.text(run.status.upper(),80,205,29,ACCENT,bold=True)
        self.lines(v["story"],80,254,730,21,TEXT)
        self.text("TOTAL SCORE",1080,205,18,MUTED,center=True)
        self.text(score["total"],1080,235,45,ACCENT,center=True,bold=True)
        self.text("PERFORMANCE",100,320,18,MUTED)
        self.text("RECORDED",720,320,18,MUTED)
        self.text("POINTS",1080,320,18,MUTED)
        self.rule(80,350,1200,350)
        for i,row in enumerate(score["rows"]):
            y = 365+i*35
            self.text(row["label"],100,y,21)
            self.text(row["value"],720,y,21,MUTED)
            self.text(f"+{row['points']}",1080,y,21,ACCENT)
        self.lines(v["message"],80,615,1120,17)
        self.text("Score formula v1 · provisional weights",390,695,16,MUTED)
        self.button("Main Menu" if self.finished else "Saving record...",(930,680,280,48),"menu",enabled=self.finished)

    def rules_page(self, page, overlay=False):
        """The same illustrated reference opens from the menu or over a live game."""
        panel = self.surface.get_rect().inflate(-52,-48)
        if overlay:
            shade = pygame.Surface(self.surface.get_size(),pygame.SRCALPHA)
            shade.fill((0,0,0,185))
            self.surface.blit(shade,(0,0))
        pygame.draw.rect(self.surface,BG,panel,border_radius=8)
        pygame.draw.rect(self.surface,LINE,panel,width=1,border_radius=8)
        self.buttons,self.die_details,self.hover = [],[],None
        self.text("SPECIAL DICE GUIDE" if page == 2 else "SCORING RULES",panel.centerx,panel.top+26,30,center=True,bold=True)
        subtitle = ("Type sets the effect. Quality strengthens biased faces; base scoring stays the same." if page == 2
                    else "Use dice from one roll. Bank saves points; Bust loses unbanked points.")
        self.text(subtitle,
                  panel.centerx,panel.top+80,19,MUTED,center=True)
        self.text(f"{page+1} / 3 · "+("SINGLES & MATCHES","STRAIGHTS & PAIRS","SPECIAL DICE")[page],
                  panel.centerx,panel.top+130,22,ACCENT,center=True)
        left,right = panel.left+66,panel.centerx+38
        data = self.rule_examples

        def dice_row(values,x,y):
            for index,face in enumerate(values):
                self.surface.blit(self.die_face(self.basic[0],face),(x+index*(DIE_SIZE+8),y))

        def example(item,x,y,score_x):
            dice_row(item["dice"],x,y)
            self.text(f"= {item['score']}",score_x,y+12,25,ACCENT,bold=True)

        if page == 0:
            self.text("THREE MATCHING DICE",left,207,18,MUTED)
            for index,item in enumerate(data["triples"]):
                example(item,left,246+index*60,left+210)
            self.text("SCORING SINGLES",right,207,18,MUTED)
            for index,item in enumerate(data["singles"]):
                example(item,right+index*250,246,right+index*250+70)
            self.text("EACH EXTRA MATCHING DIE",right,340,18,MUTED)
            example(data["triples"][2],right,380,right+188)
            self.text("+",right+276,391,25,MUTED)
            dice_row([3],right+308,380)
            self.text(f"+{data['extra_bonus']}",right+374,392,25,ACCENT,bold=True)
            self.text(f"4 matching dice = {data['extras'][0]['score']}",right,447,19,MUTED)
            for index,item in enumerate(data["extras"][1:]):
                example(item,right,486+index*68,right+370)
            note = "Only banked points reach 2000. Never combine dice from separate rolls."
        elif page == 1:
            self.text("STRAIGHTS",left,207,18,MUTED)
            for index,item in enumerate(data["straights"]):
                example(item,left,246+index*80,left+370)
            self.text("ORDINARY THREE PAIRS",left,486,18,MUTED)
            dice_row(data["ordinary_pairs"][0]["dice"],left,526)
            self.text(f"+{data['ordinary_pairs'][0]['score']} → Roll 6",left+370,542,20,ACCENT,bold=True)
            self.text("Earlier turn points are kept. Bank is unavailable.",left,592,17,MUTED)
            self.text("THREE CONSECUTIVE PAIRS",right,207,18,MUTED)
            for index,item in enumerate(data["pairs"]):
                example(item,right,246+index*80,right+370)
            self.lines("HOT DICE: scoring all six returns your original six dice. Turn points stay at risk.",
                       right,566,520,18,MUTED)
            note = "HP counts extra lives. HP=0 can still play; losing to the Boss ends the run."
        else:
            self.surface.blit(self.die_face(self.basic[0],3),(left,205))
            self.text("Basic",left+68,205,18,TEXT,bold=True)
            self.text("Fair faces 1-6; no effect.",left+68,232,16,MUTED)
            for index,(quality,die) in enumerate(self.guide_qualities.items()):
                x = right-68+index*188
                self.surface.blit(self.die_face(die,1),(x,205))
                self.text(quality.title(),x+64,205,18,TEXT,bold=True)
                self.text(f"Bias weight {max(die_weights(die))}",x+64,232,16,MUTED)
            self.text("B/S/G bands and 1/2/3 notches show quality. Other faces have weight 1.",
                      panel.centerx,264,16,MUTED,center=True)
            for index,(kind,die) in enumerate(self.guide_dice.items()):
                x,y = (left if index%2 == 0 else right),288+(index//2)*80
                face = 0 if kind in ("devil","angel") else 1
                self.surface.blit(self.die_face(die,face),(x,y+5))
                quality = "Silver only" if die.quality == "silver" else "B/S/G"
                unique = " · unique" if kind in ("devil","angel") else ""
                self.text(f"{kind.title()} · {quality}{unique}",x+68,y,18,TEXT,bold=True)
                self.lines(die_effect_text(die),x+68,y+24,456,16,MUTED)
            note = "Unique: one of each per run. Momentum resets on Bank/Bust; Rescue refreshes each battle."
        self.text(note,panel.centerx,620,17,MUTED,center=True)
        if overlay:
            self.text("AI continues in the background. Automatic turn changes wait while rules are open.",
                      panel.centerx,644,15,MUTED,center=True)
        self.rule(panel.left+54,664,panel.right-54,664)
        labels = ("Singles & matches","Straights & pairs","Special dice")
        controls = row_rects((panel.left,668,panel.width,96),4,width=260,height=48,gap=16)
        for index,label in enumerate(labels):
            self.button(label,controls[index],("rules_page",index),active=page == index)
        self.button("Close rules" if overlay else "Back",controls[-1],
                    "close_rules" if overlay else "menu")

    def leaderboard(self):
        self.header("LOCAL LEADERBOARD")
        entries,page = self.view["entries"],self.view["page"]
        self.text("Completed runs · Score formula v1",80,205,21,ACCENT)
        for x,label in ((100,"RANK"),(240,"SCORE"),(440,"RESULT"),(690,"STARTED")):
            self.text(label,x,265,18,MUTED)
        self.rule(80,300,1200,300)
        if not entries:
            self.lines("No completed scored runs yet. Finish a journey to record your score.",
                       240,370,800,24,TEXT)
        for index,entry in enumerate(entries[page*8:(page+1)*8],page*8+1):
            y = 315+(index-page*8-1)*37
            self.text(index,100,y,22,MUTED)
            self.text(entry["score"],240,y,23,ACCENT,bold=True)
            self.text(entry["status"].upper(),440,y,21)
            self.text(entry["started"].strftime("%Y-%m-%d  %H:%M:%S"),690,y,21)
        self.text("Local text logs only. Quits and older logs without scores are excluded.",80,625,17,MUTED)
        self.text(f"Runs: {len(entries)} · Page {page+1} / {max(1,(len(entries)+7)//8)}",80,683,19,MUTED)
        self.button("Previous",(660,680,170,48),("page",page-1),enabled=page>0)
        self.button("Next",(850,680,170,48),("page",page+1),enabled=(page+1)*8<len(entries))
        self.button("Back",(1040,680,170,48),"menu")

    def opening(self):
        if self.intro_art is None:
            try:
                original = pygame.image.load(INTRO_ART).convert()
                self.intro_art = pygame.transform.smoothscale(original,(480,320))
            except (OSError,pygame.error):
                self.intro_art = False
        if self.intro_art:
            self.surface.blit(self.intro_art,(70,215))
        else:
            self.text("Opening artwork unavailable",90,350,20,MUTED)
        self.lines("The dragon hoards the kingdom's golden dice.\n"
                   "Four gamblers stand between you and its lair.\n"
                   "An angel's ward can spare one defeat on the road.",600,225,600,22,TEXT)
        self.text("Reach the dragon - and know when to stop.",600,365,23,ACCENT,bold=True)
        self.lines("Boss defeat ends the run, even with a ward remaining.",600,418,570,19)
        self.lines("At the roadside shrine, three different special dice await.\nDraw them, or leave them behind.",600,477,570,19)
        rescue_chance = self.view["rescue_chance"]
        for x, label, chance in ((350,"3 different Bronze dice",f"{100-rescue_chance}%"),
                                 (930,"2 Bronze + Silver Rescue",f"{rescue_chance}%")):
            self.text(label,x,566,20,center=True)
            self.text(chance,x,598,26,ACCENT,center=True,bold=True)

    def draw(self):
        self.surface.fill(BG)
        self.buttons, self.die_details, self.hover = [], [], None
        screen = self.view["screen"]
        context = (screen, self.token, getattr(self.view.get("state"), "phase", None),
                   self.view.get("active_side"))
        if context != self.focus_context:
            self.focus_context, self.focus = context, None
        if screen == "menu":
            canvas = self.surface.get_rect()
            column = pygame.Rect(canvas.centerx-250, canvas.centery-100, 280, 273)
            self.text("THE KING'S GAMBIT", canvas.centerx, column.top-125, 43, center=True, bold=True)
            self.rule(column.left-50,column.top-50,column.right+270,column.top-50)
            for i,(label,action) in enumerate((("New Run","new_run"),("Leaderboard","leaderboard"),("Rules","rules"),("Quit","exit"))):
                self.button(label, (column.left,column.top+i*75,column.width,48), action)
            self.rule(column.right+70,column.top,column.right+70,column.bottom)
            self.die(self.basic[0], 3, column.right+160, column.centery-DIE_SIZE//2)
        elif screen == "battle":
            self.battle()
        elif screen in ("guess_roll","spinner_roll","event_result"):
            self.event_view()
        elif screen == "run_score":
            self.score_screen()
        elif screen == "leaderboard":
            self.leaderboard()
        elif screen in ("initial","wager","reward","guess_intro","guess","guess_claim","spinner","shop","run_summary"):
            self.growth()
        elif screen == "rules":
            self.rules_page(self.view["page"])
        elif screen in ("complete","error"):
            self.header("PRACTICE COMPLETE" if screen == "complete" else "GAME STOPPED")
            result = self.view.get("result")
            self.lines(self.view.get("message", f"Banked score: {result}"), 250, 300, 780, 25)
            self.button("Main Menu", (950,680,260,48), "menu")
        else:
            self.text("Starting game...", 640, 350, 27, center=True)
        if self.overlays:
            for overlay in self.overlays:
                if overlay["kind"] == "rules":
                    self.rules_page(overlay["page"],overlay=True)
                else:
                    self.exit_dialog()
        if self.returning or self.closing:
            self.buttons, self.die_details, self.hover = [], [], None
            self.text("Ending current game...", 640, 610, 23, ACCENT, center=True)
        self.draw_focus()
        if self.hover:
            die = self.hover
            desc = die_effect_text(die)
            odds = "  ".join(f"{'*' if n == 0 else n}: {p:.1%}" for n,p in face_distribution(die.kind,die.quality))
            pygame.draw.rect(self.surface, BG, (350,748,894,52))
            self.text(f"{die.kind.title()} · {die.quality.title()} | {desc}", 390, 750, 16, ACCENT)
            self.text(odds, 390, 776, 15, MUTED)
        elif self.log_path and self.view["screen"] != "menu":
            self.text(f"Log saved: {self.log_path.name}", 390, 754, 15, MUTED)

    def draw_focus(self):
        actions = [action for _, action in self.buttons]
        if self.focus not in actions:
            self.focus = next((a for a in actions if a not in ("menu","rules")), actions[0] if actions else None)
        for rect, action in self.buttons:
            if action != self.focus:
                continue
            frame = rect.inflate(10, 10)
            for x, dx in ((frame.left, 1), (frame.right, -1)):
                for y, dy in ((frame.top, 1), (frame.bottom, -1)):
                    pygame.draw.lines(self.surface, ACCENT, False,
                                      [(x,y+dy*7),(x,y),(x+dx*7,y)], 2)
        if self.hover is None:
            self.hover = next((die for action, die in self.die_details if action == self.focus), None)

    def move_focus(self, key, backwards=False):
        if not self.buttons:
            return
        actions = [action for _, action in self.buttons]
        index = actions.index(self.focus) if self.focus in actions else 0
        if key == pygame.K_TAB:
            self.focus = actions[(index+(-1 if backwards else 1)) % len(actions)]
            return
        origin = self.buttons[index][0].center
        dx, dy = {pygame.K_LEFT:(-1,0), pygame.K_RIGHT:(1,0),
                  pygame.K_UP:(0,-1), pygame.K_DOWN:(0,1)}[key]
        candidates = []
        for rect, action in self.buttons:
            x, y = rect.centerx-origin[0], rect.centery-origin[1]
            forward, across = x*dx+y*dy, abs(x*dy-y*dx)
            if forward > 0:
                candidates.append((forward+across*2, action))
        if candidates:
            self.focus = min(candidates, key=lambda item: item[0])[1]

    def mouse_position(self, pos):
        width,height = self.window.get_size()
        scale = min(width/WIDTH, height/HEIGHT)
        return ((pos[0]-(width-WIDTH*scale)/2)/scale,
                (pos[1]-(height-HEIGHT*scale)/2)/scale)

    def display(self):
        width,height = self.window.get_size()
        scale = min(width/WIDTH,height/HEIGHT)
        size = (max(1,round(WIDTH*scale)),max(1,round(HEIGHT*scale)))
        self.window.fill(BG)
        self.window.blit(pygame.transform.smoothscale(self.surface,size),
                         ((width-size[0])//2,(height-size[1])//2))
        pygame.display.flip()

    def handle_event(self, event):
        if event.type == pygame.VIDEORESIZE:
            if event.w < 960 or event.h < 600:
                self.window = pygame.display.set_mode((max(960,event.w),max(600,event.h)), pygame.RESIZABLE)
        elif event.type == pygame.QUIT:
            if self.overlays and self.overlays[-1]["kind"] == "exit":
                self.overlays[-1]["destination"] = "exit"
            else:
                self.activate("exit")
        elif event.type == pygame.KEYDOWN:
            self.draw()  # Rebuild legal controls after the previous event in this batch.
            if event.key == pygame.K_ESCAPE:
                action = ("close_rules" if self.overlays[-1]["kind"] == "rules" else "keep_playing") if self.overlays else "menu"
                self.activate(action)
            elif event.key in (pygame.K_TAB, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                self.move_focus(event.key, bool(getattr(event, "mod", 0) & pygame.KMOD_SHIFT))
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.focus is not None:
                    self.activate(self.focus)
            elif pygame.K_1 <= event.key <= pygame.K_6 and not self.overlays:
                action = ("select", event.key-pygame.K_1+1)
                if any(a == action for _, a in self.buttons):
                    self.focus = action
                    self.activate(action)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.draw()
            position = self.mouse_position(event.pos)
            for rect, action in reversed(self.buttons):
                if rect.collidepoint(position):
                    self.focus = action
                    self.activate(action)
                    break

    def run(self):
        try:
            while not self.closing or (self.session and not self.finished):
                self.poll()
                self.mouse = self.mouse_position(pygame.mouse.get_pos())
                self.draw()
                for event in pygame.event.get():
                    self.handle_event(event)
                self.display()
                self.clock.tick(60)
        finally:
            if self.session:
                self.session.close()
                self.session.thread.join()
            pygame.quit()


def run_gui(*, ai_delay=2, score_ambition=500):
    GameWindow(ai_delay=ai_delay, score_ambition=score_ambition).run()
