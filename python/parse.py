# This example prints operators from a replay.

import json
import subprocess
from pathlib import Path
import re

r6_dissect_path = Path(__file__).parent.parent / "parser" / "r6-dissect.exe"

def parseRound(input_path):
    """Gibt JSON direkt zur Konsole aus (wie r6-dissect ohne -o Parameter)"""
    output = subprocess.run([r6_dissect_path, str(input_path)], capture_output=True, text=True)
    if output.returncode == 0:
        # JSON String parsen und als Python Dictionary zurückgeben
        return json.loads(output.stdout)
    else:
        print(f"Fehler: {output.stderr}")
        return None
    
def parseMatch(input_path):
    """Gibt Match JSON direkt zur Konsole aus"""
    match_info = parseMatchInfo(input_path)
    output = subprocess.run([r6_dissect_path, str(input_path)], capture_output=True, text=True)
    if output.returncode == 0:
        match_data = json.loads(output.stdout)
        match_data["Match_Info"] = match_info
        return match_data
    else:
        print(f"Fehler: {output.stderr}")
        return None
    
def parseMatchInfo(input_path):
    """Gibt Match-Info als Dictionary zurück"""
    output = subprocess.run([r6_dissect_path, "--info", str(input_path)], capture_output=True, text=True)
    if output.returncode == 0:
        info = {}
        lines = output.stderr.strip().split('\n')
        for line in lines:
            if 'INF' in line:
                # Format: "5:20PM INF Key: Value"
                parts = line.split('INF', 1)[1].strip().split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    # ANSI-Escape-Codes entfernen
                    key = re.sub(r'\x1b\[[0-9;]*m', '', key)[1:]
                    value = re.sub(r'\x1b\[[0-9;]*m', '', value)
                    # Recording Player in Tupel aufteilen
                    if key == "Recording Player":
                        # Pattern: "Username [UUID]"
                        match = re.match(r'(.+?)\s+\[([a-f0-9\-]+)\]', value)
                        if match:
                            username = match.group(1).strip()
                            uuid = match.group(2).strip()
                            value = (username, uuid)
                    elif key == "Timestamp":
                        # Pattern: "YYYY-MM-DD HH:MM:SS +ZZZZ"
                        value = " ".join(value.split()[:-1])
                        
                    info[key] = value
        return info
    else:
        print(f"Fehler: {output.stderr}")
        return None

if __name__ == "__main__":
    # path: ../replays/
    replay_dir = Path(__file__).parent.parent / "replays"
    print(f"Suche in: {replay_dir.absolute()}")
    print(f"Ordner existiert: {replay_dir.exists()}")

    # Alle Unterordner finden
    matches = [str(f) for f in replay_dir.iterdir() if f.is_dir()]
    print(f"Gefundene Ordner: {len(matches)}")

    # Alle Ordnerpfade auflisten
    # for matchfolder in matches[0]:
    # 	for round in Path(matchfolder).iterdir():
    # 		print(parseRound(round))
    # 		break

    for matchfolder in matches:
        result = parseMatch(str(matchfolder))

        # save in folder json with matchname
        path = "json"
        match_name = matchfolder.split("\\")[-1].split(".")[0]
        with open(f"{path}/{match_name}.json", "w") as f:
            json.dump(result, f, indent=4)