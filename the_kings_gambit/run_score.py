"""Pure, replayable run scoring. Version 1 weights are provisional."""


def calculate_run_score(history):
    """Derive the same breakdown from live events or their saved JSON copy."""
    final = next((e for e in reversed(history) if e["event"] == "RUN_FINISHED"), None)
    if final is None:
        raise ValueError("finish the run before calculating its score")
    income = sum(e["amount"] for e in history if e["event"] == "COINS_EARNED")
    acquired = {e["serial"]: e["quality"] for e in history if e["event"] == "DIE_ACQUIRED"}
    counts = {quality: list(acquired.values()).count(quality) for quality in ("bronze","silver","gold")}
    turns = {(e["stage"],e["turn"]) for e in history if e["event"] == "TURN_START"}
    chains, best_bank, best_chain, one_turn = {}, 0, 0, False
    for event in history:
        if event.get("side") != "Player":
            continue
        key = event["stage"],event["turn"]
        if event["event"] == "SELECT":
            chains[key] = chains.get(key,0)+1
        elif event["event"] == "BANK":
            best_bank = max(best_bank,event["banked"])
            best_chain = max(best_chain,chains.get(key,0))
            one_turn |= event["banked"] >= final["target"]
    wins = sum(e["event"] == "STAGE_WON" for e in history)
    rows = [
        dict(label="Wards remaining",value=str(final["hp"]),points=final["hp"]*500),
        dict(label="Coins earned",value=str(income),points=income),
        dict(label="Special dice acquired",value=f"B {counts['bronze']} / S {counts['silver']} / G {counts['gold']}",
             points=counts["bronze"]*100+counts["silver"]*250+counts["gold"]*600),
        dict(label="Best banked turn",value=str(best_bank),points=best_bank//5),
        dict(label="Longest banked chain",value=str(best_chain),points=max(0,best_chain-1)*50),
        dict(label="Target in one turn",value="Yes" if one_turn else "No",points=1000 if one_turn else 0),
        dict(label="Total turns (both sides)",value=str(len(turns)),points=max(0,wins*500-len(turns)*20)),
    ]
    return dict(version=1,status=final["status"],rows=rows,total=sum(row["points"] for row in rows))
