import os
import browser_cookie3
from pathlib import Path
from dotenv import load_dotenv, set_key
import tomllib

ENV_PATH = Path.home() / ".config" / "candidate" / ".env"
CONFIG_PATH = Path.home() / ".config" / "candidate" / "config.toml"

ENV_PATH.parent.mkdir(parents=True, exist_ok=True)

load_dotenv(ENV_PATH)

BROWSER_LOADERS = [
    ("Chrome",  browser_cookie3.chrome),
    ("Brave",   browser_cookie3.brave),
    ("Firefox", browser_cookie3.firefox),
    ("Safari",  browser_cookie3.safari),
    ("Edge",    browser_cookie3.edge),
    ("Opera",   browser_cookie3.opera),
]

COOKIE_TARGETS = {
    "LC_SESSION_COOKIE": {
        "domain":      "leetcode.com",
        "cookie_name": "LEETCODE_SESSION",
        "label":       "LeetCode",
    },
    "AC_SESSION_COOKIE": {
        "domain":      "atcoder.jp",
        "cookie_name": "REVEL_SESSION",
        "label":       "AtCoder",
    },
}


def _detect_from_browsers(domain: str, cookie_name: str) -> tuple[str, str]:
    for browser_name, loader in BROWSER_LOADERS:
        try:
            cj    = loader(domain_name=domain)
            all_cookies = [(c.name, c.value[:20] + "...") for c in cj]
            print(f"[debug] {browser_name} cookies for {domain}: {all_cookies}")
            
            value = next((c.value for c in cj if c.name == cookie_name), "")
            if value:
                return value, browser_name
        except Exception:
            continue
    return "", ""


def get_cookie(env_key: str) -> str:
    target      = COOKIE_TARGETS[env_key]
    domain      = target["domain"]
    cookie_name = target["cookie_name"]
    label       = target["label"]

    existing = os.environ.get(env_key, "")
    if existing:
        print(f"[cookies] {label}: loaded from .env")
        return existing

    print(f"[cookies] {label}: scanning browsers...", end=" ", flush=True)
    value, browser_name = _detect_from_browsers(domain, cookie_name)

    if value:
        print(f"found in {browser_name}")
        set_key(ENV_PATH, env_key, value)
        os.environ[env_key] = value
        return value

    print("not found")
    print(
        f"[cookies] WARNING: Could not auto-detect {label} session cookie.\n"
        f"          Log in to {domain.lstrip('.')} in any supported browser, then re-run.\n"
        f"          Or set {env_key} manually in your .env file."
    )
    return ""


LC_SESSION_COOKIE = get_cookie("LC_SESSION_COOKIE")
AC_SESSION_COOKIE = get_cookie("AC_SESSION_COOKIE")



def _write_default_config():
    default = """\
[handles]
codeforces = ""
atcoder    = ""
leetcode   = ""

[codeforces]
tier1      = [1000, 1500]
tier2      = [1600, 1900]
recent_max = 1900

[atcoder]
tier1      = [1000, 1200]
tier2      = [1300, 1800]
recent_max = 320

[leetcode]
difficulties = ["MEDIUM", "HARD"]
recent_max   = 2500

[display]
show_difficulties = false
"""
    CONFIG_PATH.write_text(default)

def _load() -> dict:
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        print(
            f"[candidate] No config found. Created default config at:\n"
            f"  {CONFIG_PATH}\n"
            f"  Edit it to add your handles and preferences, then re-run."
        )
        _write_default_config()
        raise SystemExit(1)
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


_cfg = _load()
_handles    = _cfg.get("handles", {})
_cf         = _cfg.get("codeforces", {})
_ac         = _cfg.get("atcoder", {})
_lc         = _cfg.get("leetcode", {})
_display    = _cfg.get("display", {})

# Contest defaults (Don't change these)
DEFAULT_MINUTES = 120
NUM_PROBLEMS = 4
CHECK_INTERVAL = 30

# Handles
CF_HANDLE = _handles.get("codeforces", "")
AC_HANDLE = _handles.get("atcoder", "")
LC_HANDLE = _handles.get("leetcode", "")

# Codeforces
CF_T1     = tuple(_cf.get("tier1",      [1000, 1500]))
CF_T2     = tuple(_cf.get("tier2",      [1600, 1900]))
CF_RECENT = _cf.get("recent_max",       1900)

# AtCoder
AC_T1     = tuple(_ac.get("tier1",      [1000, 1200]))
AC_T2     = tuple(_ac.get("tier2",      [1300, 1800]))
AC_RECENT = _ac.get("recent_max",       320)

# LeetCode
LC_DIFFICULTIES = _lc.get("difficulties", ["MEDIUM", "HARD"])
LC_RECENT       = _lc.get("recent_max",   2500)

# Display
SHOW_DIFFICULTY = _display.get("show_difficulties", False)

BAR_FULL = "█"
BAR_EMPTY = "░"
URGENCY = "critical"
