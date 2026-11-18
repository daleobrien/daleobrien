"""Decide whether the face is awake or asleep, and update status.json and README.md.

EVENT is the GitHub event name; ACTION is the repository_dispatch type ("sleep" or "wake").
A phone event always sets the face. The clock only nudges it: from 10pm it goes to sleep
if it isn't already asleep, and from 7am it wakes up if it isn't already awake. At any
other time a scheduled run does nothing.
"""

import json
import os
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

MELBOURNE = ZoneInfo("Australia/Melbourne")
SLEEP_HOURS = (22, 23)  # 10pm and 11pm: go to sleep if still awake
WAKE_HOURS = (7, 8)  # 7am and 8am: wake up if still asleep
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
    hour = now.astimezone(MELBOURNE).hour
    if hour in SLEEP_HOURS:
        state = "asleep"
    elif hour in WAKE_HOURS:
        state = "awake"
    else:
        print(f"{hour}:00 in Melbourne is outside the sleep and wake windows, nothing to do")
        raise SystemExit(0)
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
