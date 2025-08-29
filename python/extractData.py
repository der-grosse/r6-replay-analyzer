from math import e
from tkinter import ROUND
from pyparsing import C
from mapFunctions import map_maps

global REFRAGTIME, prep_duration, round_duration, plant_duration
REFRAGTIME = 7  # seconds
prep_duration = 45
round_duration = 180
plant_duration = 45

def correct_data(data: dict) -> dict:
    #remove key "stats"
    data.pop("stats", None)
    # Check if last round(s) are valid
    keep_index = len(data["rounds"])
    for i, round in enumerate(reversed(data["rounds"])):
        if len(round["stats"]) < 1:
            keep_index -= 1
        else:
            break
    data["rounds"] = data["rounds"][:keep_index]
    return data

def extract_time_stamp(data: dict) -> str:
    date, time, offset = data["Match_Info"]["Timestamp"].split(" ")
    offset_hour, offset_minute = int(offset[1:3]), int(offset[3:5])
    hour, minute, second = map(int, time.split(":"))
    if offset[0] == "+":
        hour -= offset_hour
        minute -= offset_minute
    elif offset[0] == "-":
        hour += offset_hour
        minute += offset_minute
    return f"{date} {hour:02}:{minute:02}:{second:02}"
    
def extract_data(data: dict) -> dict["match_data": dict, "player_data": dict, 
                                     "rounds_data": dict, "player_rounds_data": dict, 
                                     "player_match_data": dict, "events_data": list[dict]]:
    data = correct_data(data)
    match_data = extract_match_data(data)
    player_data = extract_player_data(data)
    player_rounds_data = extract_player_rounds_data(data)
    player_match_data = extract_player_match_data(data)
    events_data = extract_events_data(data, player_data)
    rounds_data = extract_rounds_data(data, events_data)
    return {"match_data": match_data, "player_data": player_data, "rounds_data": rounds_data, "player_rounds_data": player_rounds_data, "player_match_data": player_match_data, "events_data": events_data}

def extract_match_data(data: dict) -> dict:
    match_info = data["Match_Info"]
    ID = match_info["Match ID"]
    RECORDING_PLAYER_UBISOFT_ID = match_info["Recording Player"][1]
    # Extract the date, time, and offset from the timestamp and add offset to time
    TIMESTAMP = extract_time_stamp(data)
    GAMEMODE = match_info["Game Mode"]
    map_id = data["rounds"][0]["map"]["id"]
    MAP = map_maps(map_id)
    MATCHTYPE = match_info["Match Type"]
    GAMEVERSION = match_info["Version"]
    # Extract winner Team index
    last_round_teams = data["rounds"][-1]["teams"]
    score_team_0 = last_round_teams[0]["score"]
    score_team_1 = last_round_teams[1]["score"]
    if score_team_0 > score_team_1:
        WINNER_TEAM_INDEX = 0
    elif score_team_0 < score_team_1:
        WINNER_TEAM_INDEX = 1
    else:
        WINNER_TEAM_INDEX = None
    TEAM0STARTINGSIDE = "ATK" if data["rounds"][0]["teams"][0]["role"] == "Attack" else "DEF"

    return {"match_id": ID, 
            "player_id": RECORDING_PLAYER_UBISOFT_ID, 
            "timestamp": TIMESTAMP, 
            "game_mode": GAMEMODE, 
            "map": MAP, 
            "match_type": MATCHTYPE, 
            "game_version": GAMEVERSION, 
            "team_id": None, 
            "winner_team_index": WINNER_TEAM_INDEX,
            "team0_starting_side": TEAM0STARTINGSIDE
            }

def extract_player_data(data: dict) -> dict:
    player_dict = {}
    TIMESTAMP = extract_time_stamp(data)
    for round in data["rounds"]:
        for player in round["players"]:
            UBISOFTID = player["profileID"]
            if UBISOFTID in player_dict:
                continue
            else:
                USERNAME = player["username"]
                TEAMID = None
                player_dict[UBISOFTID] = {"ubisoft_id": UBISOFTID, 
                                          "username": USERNAME, 
                                          "timestamp": TIMESTAMP, 
                                          "team_id": TEAMID}
        if len(player_dict) == 10:
            break
    return player_dict

def extract_rounds_data(data: dict, events_data: dict) -> list[dict]:
    rounds_data = []
    match_info = data["Match_Info"]
    ID = match_info["Match ID"]
    for i, round in enumerate(data["rounds"]):
        ROUNDNUMBER = i + 1
        SITE = round["site"]
        WINNERTEAMINDEX = 0 if round["teams"][0]["won"] else 1
        ATKTEAMINDEX = 0 if round["teams"][0]["role"] == "Attack" else 1
        DEFTEAMINDEX = 1 - ATKTEAMINDEX
        # Find All Events of this Round
        events_of_round = [event for event in events_data if event["round_number"] == ROUNDNUMBER]
        TIMETOENTRY = None
        OKTEAMINDEX = None
        OKREFRAG = False
        WINCONDITION = "time"
        CLUTCH = False
        clutch_situation = None
        team0_player_count = [p["profileID"] for p in round["players"] if p["teamIndex"] == 0]
        team1_player_count = [p["profileID"] for p in round["players"] if p["teamIndex"] == 1]
        for i, event in enumerate(events_of_round):
            # CLUTCH & OK TEAM INDEX
            if event["type"] == "Kill" and event["target_player_ubisoft_id"] in team0_player_count:
                if OKTEAMINDEX is None:
                    OKTEAMINDEX = 1
                team0_player_count.remove(event["target_player_ubisoft_id"])
                if len(team0_player_count) == 1 and clutch_situation is None:
                    if WINNERTEAMINDEX == 0:
                        CLUTCH = True
                        clutch_situation = True
            if event["type"] == "Kill" and event["target_player_ubisoft_id"] in team1_player_count:
                if OKTEAMINDEX is None:
                    OKTEAMINDEX = 0
                team1_player_count.remove(event["target_player_ubisoft_id"])
                if len(team1_player_count) == 1 and clutch_situation is None:
                    if WINNERTEAMINDEX == 1:
                        CLUTCH = True
                        clutch_situation = True
            elif event["type"] == "Kill" and event["target_player_ubisoft_id"] in team1_player_count:
                team1_player_count.remove(event["target_player_ubisoft_id"])

            # WINCONDITION
            if event["type"] == "DefuserPlantComplete":
                WINCONDITION = "plant"
            if (len(team0_player_count) == 0 or len(team1_player_count) == 0) and WINCONDITION == "time":
                WINCONDITION = "kills"

            # OK REFRAG
            if event["type"] == "Kill":
                for next_event in events_of_round[i+1:]:
                    if next_event["type"] == "Kill" and next_event["target_player_ubisoft_id"] == event["player_ubisoft_id"]:
                        if next_event["refrag"]:
                            if OKREFRAG is None:
                                OKREFRAG = True
                                break

            # Time to entry
            if event["type"] == "Kill" and TIMETOENTRY is None:
                TIMETOENTRY = event["time_elapsed_seconds"]
        rounds_data.append({"match_id":ID,
                            "round_number":ROUNDNUMBER,
                            "site":SITE,
                            "winner_team_index":WINNERTEAMINDEX,
                            "atk_team_index":ATKTEAMINDEX,
                            "def_team_index":DEFTEAMINDEX,
                            "time_to_entry":TIMETOENTRY,
                            "ok_team_index":OKTEAMINDEX,
                            "ok_refrag":OKREFRAG,
                            "clutch":CLUTCH,
                            "win_condition":WINCONDITION,
                            })
    return rounds_data

def extract_player_rounds_data(data: dict) -> list[dict]:
    pass

def extract_player_match_data(data: dict) -> list[dict]:
    pass

def extract_events_data(data: dict, player_data: dict) -> list[dict]:
    events = []
    for i, round in enumerate(data["rounds"]):
        ROUNDNUMBER = i + 1
        # Give each event a phase
        event_list = round["matchFeedback"]
        plant_down = False
        prep_index = None
        plant_time = None
        for j, event in enumerate(round["matchFeedback"]):
            match event["type"]["name"]:
                case "OperatorSwap":
                    phase = "prep"
                    prep_index = j
                case "Kill":
                    phase = "round" if not plant_down else "plant"
                case "Death":
                    phase = "round" if not plant_down else "plant"
                case "DefuserPlantComplete":
                    phase = "round"
                    plant_down = True
                    plant_time = round_duration - event["timeInSeconds"] if round_duration - event["timeInSeconds"] >= 0 else 0
                case "DefuserDisableComplete":
                    phase = "plant"
                case _:
                    phase = "unknown"
            
            event_list[j]["phase"] = phase

        if prep_index is not None:
            for j in range(prep_index+1):
                event_list[j]["phase"] = "prep"
        # extract event data
        for event in event_list:
            username = event["username"]
            UBISOFTID = [uid for uid, info in player_data.items() if info["username"] == username][0]
            target_username = event.get("target")
            TARGETUBISOFTID = [uid for uid, info in player_data.items() if info["username"] == target_username][0] if target_username else None
            TYPE = event["type"]["name"]
            PHASE = event["phase"]
            match PHASE:
                case "prep":
                    start_time = prep_duration
                case "round":
                    start_time = round_duration
                case "plant":
                    start_time = plant_duration
            event_time = event["timeInSeconds"]
            TIMEELAPSEDSECONDS = start_time - event_time if start_time - event_time >= 0 else 0
            # Refrag True if Killer dies within X seconds
            REFRAG = False
            if TYPE == "Kill":
                for earlier_event in reversed(events):
                    if earlier_event["type"] == "Kill":
                        past_event_time = earlier_event["time_elapsed_seconds"]
                        
                        # Check if the TARGET of current kill was the KILLER in the earlier event
                        if earlier_event["player_ubisoft_id"] == TARGETUBISOFTID:
                            if earlier_event["phase"] == event["phase"]:
                                # Same phase - simple time difference check
                                time_diff = TIMEELAPSEDSECONDS - past_event_time
                                if time_diff <= REFRAGTIME and time_diff >= 0:
                                    REFRAG = True
                                    print(f"REFRAG: diff {time_diff}\n  1st {past_event_time} {earlier_event['phase']}\n  2nd {TIMEELAPSEDSECONDS} {event['phase']}")
                                    break
                                elif time_diff < 0:
                                    # Events are out of order, stop looking
                                    break
                            elif earlier_event["phase"] == "round" and event["phase"] == "plant":
                                # Transition from round to plant phase
                                if plant_time is not None:
                                    # Time from earlier kill to plant + time from plant start to current kill
                                    time_diff = (round_duration - past_event_time) + TIMEELAPSEDSECONDS
                                    if time_diff <= REFRAGTIME:
                                        REFRAG = True
                                        print(f"REFRAG: diff {time_diff}\n  1st {past_event_time} {earlier_event['phase']}\n  2nd {TIMEELAPSEDSECONDS} {event['phase']} planttime:{plant_time}")
                                        break
                            # If we've gone too far back in time, stop searching
                            elif earlier_event["phase"] != event["phase"]:
                                break
            
            OPERATOR = event.get("operator")["name"] if event.get("operator") else None
            events.append({"round_number": ROUNDNUMBER,
                           "player_ubisoft_id": UBISOFTID,
                           "target_player_ubisoft_id": TARGETUBISOFTID,
                           "type": TYPE,
                           "phase": PHASE,
                           "time_elapsed_seconds": TIMEELAPSEDSECONDS,
                           "refrag": REFRAG,
                           "operator": OPERATOR
                           })
    return events

if __name__ == "__main__":
    from json import load
    from time import perf_counter as pc
    from pathlib import Path

    match_name = "Match-2025-07-17_20-54-09-3448"
    with open(Path(__file__).parent.parent / "data" / "json" / f"{match_name}.json", "r") as f:
        data = load(f)
    
    start = pc()
    r_counter = 0
    extracted_data = extract_data(data)
    # print(f"Extraction took {pc() - start:.2f} seconds")
    # for key, value in extracted_data.items():
    #     print(f"{key}: {type(value)} with {len(value.items()) if isinstance(value, dict) else '1'} entries")
    #     if isinstance(value, dict):
    #         for k, v in value.items():
    #             print(f"  {k}: {v}")
    #     if key == "rounds_data":
    #         for round in value:
    #             print(round)

