import requests
import time
import json

url = "https://raw.githubusercontent.com/o-daneel/Lunii.RE/main/resources/packs.json"
response = requests.get(url).json()

results = []

for key in response["response"]:
    entry = response["response"][key]
    localized_infos = entry.get("localized_infos", {}).get("fr_FR", {})
    if not localized_infos:
        continue
    else:
        title = localized_infos.get("title", "")
    result = {
        "uuid": entry.get("uuid", ""),
        "title": title,
        "keywords": entry.get("keywords", ""),
        "subtitle": entry.get("subtitle", ""),
    }
    results.append(result)



json.dump(results, open("titles.json", "w"), indent=4)