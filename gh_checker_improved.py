#!/usr/bin/env python3
from typing import Optional, List, Tuple
"""
GitHub Username Availability Checker
Generates and checks random usernames against the GitHub API.
Uses a Personal Access Token for 5 000 req/hr instead of 60.
"""

import random
import string
import time
import urllib.request
import urllib.error

#COLOURS
RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
DIM    = "\033[2m"

#very important dont touch this or it WILL break.
GITHUB_TOKEN: Optional[str] = None


#GEN section

def generate_usernames(pattern: str, count: int = 20) -> List[str]:
    letters  = string.ascii_lowercase
    digits   = string.digits
    alphanum = letters + digits
    results: set[str] = set()

    def mixed(length: int) -> str:
        while True:
            c = "".join(random.choices(alphanum, k=length))
            if any(ch in digits for ch in c) and any(ch in letters for ch in c):
                return c

    generators = {
        "3_letter":       lambda: "".join(random.choices(letters, k=3)),
        "3_alphanumeric": lambda: mixed(3),
        "4_letter":       lambda: "".join(random.choices(letters, k=4)),
        "4_alphanumeric": lambda: mixed(4),
    }

    gen = generators[pattern]
    attempts = 0
    while len(results) < count and attempts < count * 20:
        results.add(gen())
        attempts += 1
    return list(results)


#GITHUB API

def check_github_username(username: str) -> Tuple[str, Optional[int]]:
    """
    Returns (status, rate_limit_remaining).
    status: 'available' | 'taken' | 'rate_limited' | 'error'
    """
    url = f"https://api.github.com/users/{username}"
    headers = {
        "User-Agent": "github-username-checker/1.0",
        "Accept":     "application/vnd.github+json",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            remaining = resp.headers.get("X-RateLimit-Remaining")
            remaining = int(remaining) if remaining is not None else None
            return ("taken", remaining)
    except urllib.error.HTTPError as e:
        remaining = e.headers.get("X-RateLimit-Remaining")
        remaining = int(remaining) if remaining is not None else None
        if e.code == 404:
            return ("available", remaining)
        if e.code in (403, 429):
            return ("rate_limited", remaining)
        return ("error", remaining)
    except Exception:
        return ("error", None)


#UI

BANNER = f"""
{CYAN}{BOLD}╔══════════════════════════════════════════╗
║   GitHub Username Availability Checker   ║
╚══════════════════════════════════════════╝{RESET}
"""

print("Hey, Mirage here. I just wanted to say that if you dont have a token, youll only be able to produce 60 generations per hour, which is really bad. I hightly recommend you create a free Github token (i could speedrun it in 20 seconds 😎) but with a token you can make 5000 gens per hour!")
TOKEN_PROMPT = f"""
{YELLOW}{BOLD}GitHub API Rate Limit{RESET}
Without a token  →  {RED}60 requests / hour{RESET}  (hits limit almost immediately)
With a token     →  {GREEN}5 000 requests / hour{RESET}

To create a free token (no special scopes needed):
  {DIM}https://github.com/settings/tokens/new{RESET}
  Scroll to the bottom and click "Generate token" — no boxes need to be ticked.

"""

MENU = f"""
{BOLD}Choose a username pattern:{RESET}

  {CYAN}1{RESET}  →  3 letters only   (e.g. {DIM}abc{RESET})
  {CYAN}2{RESET}  →  3 chars, mixed   (e.g. {DIM}e7r{RESET} / {DIM}u62{RESET})
  {CYAN}3{RESET}  →  4 letters only   (e.g. {DIM}abcd{RESET})
  {CYAN}4{RESET}  →  4 chars, mixed   (e.g. {DIM}s8de{RESET} / {DIM}o40c{RESET})
  {CYAN}q{RESET}  →  quit
"""

PATTERN_MAP = {
    "1": "3_letter",       "3 letter": "3_letter",   "3 letters": "3_letter",
    "2": "3_alphanumeric", "3 mixed":  "3_alphanumeric", "3 alphanumeric": "3_alphanumeric",
    "3": "4_letter",       "4 letter": "4_letter",   "4 letters": "4_letter",
    "4": "4_alphanumeric", "4 mixed":  "4_alphanumeric", "4 alphanumeric": "4_alphanumeric",
    "3 letter and number":  "3_alphanumeric",
    "4 letter and number":  "4_alphanumeric",
    "3 letter number":      "3_alphanumeric",
    "4 letter number":      "4_alphanumeric",
}

PATTERN_LABELS = {
    "3_letter":       "3-letter",
    "3_alphanumeric": "3-char mixed (letters + digits)",
    "4_letter":       "4-letter",
    "4_alphanumeric": "4-char mixed (letters + digits)",
}


def ask_for_token() -> None:
    global GITHUB_TOKEN
    print(TOKEN_PROMPT)
    raw = input(f"{BOLD}Paste your GitHub token (or press Enter to skip):{RESET} ").strip()
    if raw:
        GITHUB_TOKEN = raw
        print(f"\n{GREEN}✔ Token saved — using authenticated requests (5 000/hr).{RESET}\n")
    else:
        print(f"\n{YELLOW}⚠  No token — limited to 60 requests/hr. You will hit the rate limit quickly.{RESET}\n")


def ask_count() -> int:
    while True:
        raw = input(f"\n{BOLD}How many to generate and check?{RESET} [{DIM}default 20{RESET}]: ").strip()
        if raw == "":
            return 20
        try:
            n = int(raw)
            if 1 <= n <= 500:
                return n
            print(f"{YELLOW}Please enter 1–500.{RESET}")
        except ValueError:
            print(f"{YELLOW}Invalid number.{RESET}")


def run_check(pattern_key: str, count: int) -> None:
    label = PATTERN_LABELS[pattern_key]
    print(f"\n{BOLD}Checking {count} {label} usernames…{RESET}\n")

    usernames = generate_usernames(pattern_key, count)
    available: list[str] = []
    taken:     list[str] = []
    skipped:   list[str] = []

    for i, uname in enumerate(usernames, 1):
        status, remaining = check_github_username(uname)

        rl_suffix = f"  {DIM}({remaining} left){RESET}" if remaining is not None else ""

        if status == "available":
            tag = f"{GREEN}✔ AVAILABLE{RESET}"
            available.append(uname)
            print(f"  [{i:>3}/{count}]  {BOLD}{uname:<10}{RESET}  {tag}{rl_suffix}")

        elif status == "taken":
            tag = f"{RED}✘ taken    {RESET}"
            taken.append(uname)
            print(f"  [{i:>3}/{count}]  {BOLD}{uname:<10}{RESET}  {tag}{rl_suffix}")

        elif status == "rate_limited":
            print(f"  [{i:>3}/{count}]  {BOLD}{uname:<10}{RESET}  {YELLOW}⚠ rate limited{RESET}{rl_suffix}")
            print(f"\n  {YELLOW}Rate limit hit — waiting 60 s then retrying…{RESET}\n")
            time.sleep(60)
            status2, remaining2 = check_github_username(uname)
            rl2 = f"  {DIM}({remaining2} left){RESET}" if remaining2 is not None else ""
            if status2 == "available":
                available.append(uname)
                print(f"  {GREEN}  ↳ retry: AVAILABLE{RESET}{rl2}")
            elif status2 == "taken":
                taken.append(uname)
                print(f"  {RED}  ↳ retry: taken{RESET}{rl2}")
            else:
                skipped.append(uname)
                print(f"  {YELLOW}  ↳ still failing — skipped{RESET}")
            continue

        else:
            tag = f"{YELLOW}? error    {RESET}"
            skipped.append(uname)
            print(f"  [{i:>3}/{count}]  {BOLD}{uname:<10}{RESET}  {tag}")

        time.sleep(0.85)  #speed of generation!

    #SUM
    print(f"\n{BOLD}{'─'*46}{RESET}")
    print(f"{BOLD}Results — {label}:{RESET}")
    print(f"  {GREEN}Available : {len(available)}{RESET}")
    print(f"  {RED}Taken     : {len(taken)}{RESET}")
    if skipped:
        print(f"  {YELLOW}Skipped   : {len(skipped)}{RESET}")

    if available:
        print(f"\n{GREEN}{BOLD}🎉 Available usernames:{RESET}")
        for u in available:
            print(f"   {GREEN}→  {u:<10}{RESET}  https://github.com/{u}")
    else:
        print(f"\n{YELLOW}No available usernames found. Try again for a fresh batch!{RESET}")


#ENTRY POINT

def main() -> None:
    print(BANNER)
    ask_for_token()

    while True:
        print(MENU)
        raw = input(f"{BOLD}Your choice:{RESET} ").strip().lower()

        if raw in ("q", "quit", "exit"):
            print(f"\n{DIM}Goodbye!{RESET}\n")
            break

        pattern_key = PATTERN_MAP.get(raw)
        if pattern_key is None:
            print(f"{YELLOW}Unrecognised input. Please try again.{RESET}")
            continue

        count = ask_count()
        run_check(pattern_key, count)

        again = input(f"\n{BOLD}Check another pattern? (y/n):{RESET} ").strip().lower()
        if again not in ("y", "yes"):
            print(f"\n{DIM}Goodbye!{RESET}\n")
            break


if __name__ == "__main__":
    main()