"""Decide which face to show, and update status.json and README.md.

EVENT is the GitHub event name and ACTION is the repository_dispatch type, sent by the
iPhone Shortcuts automations when a Focus turns on or off:

  <mode>      a Focus turned on: show that mode's face (sleep is an alias for asleep)
  <mode>-off  a Focus turned off: back to awake, but only if that mode is still showing
              (wake is an alias for asleep-off)

The clock only nudges the face: from 10pm it goes to sleep if it isn't asleep already,
and from 7am it wakes up if it's still asleep. Other scheduled runs do nothing.
Modes other than asleep and awake carry an "expires" time, after which the web page
shows awake in case the phone never sent the "off".
"""

import json
import os
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

MELBOURNE = ZoneInfo("Australia/Melbourne")
SLEEP_HOURS = (22, 23)  # 10pm and 11pm: go to sleep if not asleep already
WAKE_HOURS = (7, 8)  # 7am and 8am: wake up if still asleep
STATUS = "status.json"
README = "README.md"

# state: (words after "Dale is" in the README alt text, hours before it lapses to awake)
STATES = {
    "awake": ("awake", None),
    "asleep": ("asleep", None),
    "work": ("at work", 12),
    "driving": ("driving", 3),
    "fitness": ("working out", 3),
    "gaming": ("gaming", 6),
    "reading": ("reading", 4),
    "mindfulness": ("being mindful", 2),
    "dnd": ("heads down", 8),
    "personal": ("free", 12),
}
ALIASES = {"sleep": "asleep", "wake": "asleep-off"}

now = datetime.now(timezone.utc).replace(microsecond=0)

try:
    with open(STATUS) as f:
        status = json.load(f)
except FileNotFoundError:
    status = {}
current = status.get("state", "awake")

event = os.environ.get("EVENT", "")
action = os.environ.get("ACTION", "")
action = ALIASES.get(action, action)

if event == "repository_dispatch":
    source = "phone"
    if action.endswith("-off"):
        mode = action.removesuffix("-off")
        if mode not in STATES:
            raise SystemExit(f"Unknown mode {mode!r}")
        if current != mode:
            print(f"{mode} turned off, but showing {current}, so leaving it")
            raise SystemExit(0)
        state = "awake"
    elif action in STATES:
        state = action
    else:
        raise SystemExit(f"Unknown event {action!r}")
else:
    source = "clock"
    hour = now.astimezone(MELBOURNE).hour
    if hour in SLEEP_HOURS:
        state = "asleep"
    elif hour in WAKE_HOURS and current == "asleep":
        state = "awake"
    else:
        print(f"Nothing to do at {hour}:00 in Melbourne while {current}")
        raise SystemExit(0)

if current == state and status:
    if source == "phone":
        status.update(source="phone", updated=now.isoformat())
    else:
        print(f"Already {state}")
        raise SystemExit(0)
else:
    status = {"state": state, "since": now.isoformat(), "updated": now.isoformat(), "source": source}
    lapse = STATES[state][1]
    if lapse:
        status["expires"] = (now + timedelta(hours=lapse)).isoformat()

with open(STATUS, "w") as f:
    json.dump(status, f, indent=2)
    f.write("\n")

with open(README) as f:
    readme = f.read()
readme = re.sub(r"faces/[a-z]+-(light|dark)\.svg", rf"faces/{state}-\1.svg", readme)
readme = re.sub(r'alt="Dale is [^"]*"', f'alt="Dale is {STATES[state][0]}"', readme)
with open(README, "w") as f:
    f.write(readme)

print(f"{state} (from {source})")
