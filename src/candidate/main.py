import sys
import time
import subprocess
from datetime import datetime, timedelta

from . import config
from .ui import (
    tw, clr, clear_screen, draw_banner, draw_contest, draw_done,
    platform_badge, diff_colour, hyperlink, fmt, C
)
from .fetchers import (
    cf_fetch_problems, ac_fetch_problems, lc_fetch_problems,
    mixed_fetch_problems, sample_problems
)
from .tracker import SolveTracker

def send_notification(msg_title, msg_body):
    try:
        subprocess.Popen(["notify-send", "--urgency", config.URGENCY,
                          "--app-name", "CP Timer", msg_title, msg_body])
    except FileNotFoundError:
        pass

def prompt_setup():
    width = tw()
    clear_screen()
    print()
    draw_banner(width)
    print()

    print(clr("  CONTEST SETUP", C.WHITE, C.BOLD))
    print(clr("  " + "─" * 40, C.GREY))
    print()

    def ask(prompt, default=None):
        suffix = f" [{default}]" if default is not None else ""
        val = input(clr(f"  {prompt}{suffix}: ", C.CYAN)).strip()
        return val if val else str(default)

    platform = ask("Platform (cf / ac / lc / x for mixed)", "lc").lower()
    while platform not in ("cf", "ac", "lc", "x"):
        print(clr("  Invalid. Choose cf, ac, lc, or x.", C.RED))
        platform = ask("Platform", "lc").lower()

    mins_raw = ask("Time limit (minutes)", config.DEFAULT_MINUTES)
    try:
        total = int(mins_raw) * 60
    except ValueError:
        total = config.DEFAULT_MINUTES * 60

    num_raw = ask("Number of problems", config.NUM_PROBLEMS)
    try:
        num = int(num_raw)
    except ValueError:
        num = config.NUM_PROBLEMS

    tags_raw = ask("Filter tags (comma-separated, or leave blank)", "")
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []

    print()
    print(clr(f"  Fetching problems from {platform.upper()}...", C.YELLOW))
    print()

    if platform == "cf":
        t1, t2 = cf_fetch_problems(tags)
    elif platform == "ac":
        t1, t2 = ac_fetch_problems(tags)
    elif platform == "lc":
        t1, t2 = lc_fetch_problems(tags)
    else:
        t1, t2 = mixed_fetch_problems(tags)

    print(clr(f"  Pool: {len(t1)} tier-1 + {len(t2)} tier-2 candidates", C.GREY))

    if not t1 and not t2:
        print(clr("  No problems found. Check handles / cookie / tags.", C.RED))
        sys.exit(1)

    problems = sample_problems(t1, t2, num)

    if not problems:
        print(clr("  Could not sample enough problems.", C.RED))
        sys.exit(1)

    print(clr(f"  Selected {len(problems)} problems.", C.GREEN))
    print()

    clear_screen()
    print()
    draw_banner(width)
    print()
    print(clr("  CONTEST PREVIEW", C.WHITE, C.BOLD))
    print(clr("  " + "─" * 40, C.GREY))
    print()
    print(clr(f"  Platform : {platform.upper()}", C.GREY))
    print(clr(f"  Duration : {total // 60} min", C.GREY))
    print(clr(f"  Problems : {len(problems)}", C.GREY))
    print()
    print(clr("  " + "─" * 40, C.GREY))
    
    for i, prob in enumerate(problems):
        badge = platform_badge(prob["platform"])
        title_link = hyperlink(prob["url"], prob["title"])
        num_str   = clr(f"  {i+1:>2}.", C.GREY)
        title = clr(title_link, C.WHITE)
        diff  = clr(f"  {prob['difficulty']}", diff_colour(prob["difficulty"])) if config.SHOW_DIFFICULTY else ""
        print(f"{num_str} {badge} {title}{diff}")
    print()
    print(clr("  " + "─" * 40, C.GREY))
    print()
    print(clr("  Press Enter to start the contest, Ctrl+C to abort.", C.CYAN))
    print()
    try:
        input()
    except KeyboardInterrupt:
        print(clr("\n  Aborted.\n", C.GREY))
        sys.exit(0)

    return problems, total

def run():
    problems, total = prompt_setup()

    start_dt = datetime.now()
    end_dt   = start_dt + timedelta(seconds=total)

    tracker = SolveTracker(problems, start_dt)
    tracker.start()

    print("\033[?25l", end="", flush=True)

    try:
        while True:
            elapsed = (datetime.now() - start_dt).total_seconds()
            status, solve_times, last_check = tracker.snapshot()

            width = tw()
            clear_screen()
            print()
            draw_banner(width)
            print()

            frame = draw_contest(elapsed, total, start_dt, end_dt,
                                 problems, status, solve_times, last_check, width)
            print("\n".join(frame), flush=True)

            if elapsed >= total:
                send_notification("Contest Over", f"Time's up! {sum(status.values())}/{len(problems)} solved.")
                break

            if tracker.all_solved():
                send_notification("Contest Complete!", f"All {len(problems)} problems solved in {fmt(elapsed)}!")
                break

            time.sleep(1)

        # Final results
        elapsed = (datetime.now() - start_dt).total_seconds()
        status, solve_times, _ = tracker.snapshot()
        tracker.stop()

        clear_screen()
        print()
        draw_banner(tw())
        print()
        lines = draw_done(problems, solve_times, elapsed, total, tw())
        print("\n".join(lines))
        print("\a", end="", flush=True)

    except KeyboardInterrupt:
        elapsed = (datetime.now() - start_dt).total_seconds()
        status, solve_times, _ = tracker.snapshot()
        tracker.stop()

        clear_screen()
        print()
        draw_banner(tw())
        print()
        lines = draw_done(problems, solve_times, elapsed, total, tw())
        print("\n".join(lines))
        print(clr("\n  Quit early.\n", C.GREY))

    finally:
        print("\033[?25h", end="", flush=True)   # restore cursor

if __name__ == "__main__":
    run()