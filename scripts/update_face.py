"""Decide whether the face is awake or asleep, and update status.json and README.md.

EVENT is the GitHub event name; ACTION is the repository_dispatch type ("sleep" or "wake").
A phone event always wins. The clock (awake 7am-7pm Melbourne time) is only a fallback
for when the phone hasn't reported for FALLBACK_AFTER.
"""

import json
import os
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

MELBOURNE = ZoneInfo("Australia/Melbourne")
FALLBACK_AFTER = timedelta(hours=16)
STATUS = "status.json"
README = "README.md"

now = datetime.now(timezone.utc).replace(microsecond=0)

try:
    with open(STATUS) as f:
        status = json.load(f)
except FileNotFoundError:
    status = {}

event = os.environ.get("EVENT", "")
action = os.environ.get("ACTION", "")

if event == "repository_dispatch" and action in ("sleep", "wake"):
    state = "asleep" if action == "sleep" else "awake"
    source = "phone"
else:
    last = status.get("updated")
    if status.get("source") == "phone" and last:
        if now - datetime.fromisoformat(last) < FALLBACK_AFTER:
            print("Phone reported recently, leaving the face alone")
            raise SystemExit(0)
    hour = now.astimezone(MELBOURNE).hour
    state = "awake" if 7 <= hour < 19 else "asleep"
    source = "clock"

if status.get("state") == state:
    # Same face. A phone report still refreshes "updated" so the clock fallback stays off.
    if source == "phone":
        status.update(source="phone", updated=now.isoformat())
    else:
        print(f"Already {state}")
        raise SystemExit(0)
else:
    status = {"state": state, "since": now.isoformat(), "updated": now.isoformat(), "source": source}

with open(STATUS, "w") as f:
    json.dump(status, f, indent=2)
    f.write("\n")

with open(README) as f:
    readme = f.read()
readme = re.sub(r"faces/(awake|asleep)-", f"faces/{state}-", readme)
readme = re.sub(r"Dale is (awake|asleep)", f"Dale is {state}", readme)
with open(README, "w") as f:
    f.write(readme)

print(f"{state} (from {source})")
