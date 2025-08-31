mapMappingDict = {"407193663917": "Clubhouse",
                  "378595635123": "Nighthaven Labs",
                  "276279025182": "Skyscraper",
                  "379218689149": "Consulate",
                  "388073319671": "Lair"}

def map_maps(data: int)-> str:
    return mapMappingDict.get(str(data), "Unknown Map")