import shutil
from datetime import datetime
from .config import BAR_FULL, BAR_EMPTY, SHOW_DIFFICULTY, CHECK_INTERVAL

class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    WHITE  = "\033[97m"
    CYAN   = "\033[96m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    GREY   = "\033[90m"
    BLUE   = "\033[94m"

def clr(text, *codes):
    return "".join(codes) + text + C.RESET

def hyperlink(url, text):
    return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"

def tw():
    return shutil.get_terminal_size((80, 24)).columns

def fmt(seconds):
    seconds = max(0, int(seconds))
    h, r = divmod(seconds, 3600)
    m, s = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def clear_screen():
    print("\033[2J\033[H", end="", flush=True)

BANNER = [
    "  ██████╗██████╗     ████████╗██╗███╗   ███╗███████╗██████╗ ",
    " ██╔════╝██╔══██╗       ██╔══╝██║████╗ ████║██╔════╝██╔══██╗",
    " ██║     ██████╔╝       ██║   ██║██╔████╔██║█████╗  ██████╔╝",
    " ██║     ██╔═══╝        ██║   ██║██║╚██╔╝██║██╔══╝  ██╔══██╗",
    " ╚██████╗██║            ██║   ██║██║ ╚═╝ ██║███████╗██║  ██║",
    "  ╚═════╝╚═╝            ╚═╝   ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝",
]

def draw_banner(width):
    bw  = max(len(l) for l in BANNER)
    pad = max(0, (width - bw) // 2)
    for line in BANNER:
        print(clr(" " * pad + line, C.CYAN, C.BOLD))

def progress_bar(elapsed, total, width):
    ratio  = min(elapsed / total, 1.0) if total else 1.0
    filled = int(ratio * width)
    colour = C.GREEN if ratio < 0.5 else (C.YELLOW if ratio < 0.8 else C.RED)
    return clr(BAR_FULL * filled, colour, C.BOLD) + clr(BAR_EMPTY * (width - filled), C.GREY)

def diff_colour(diff_str):
    d = diff_str.upper()
    if d in ("EASY",) or (d.isdigit() and int(d) < 1200):
        return C.GREEN
    if d in ("MEDIUM",) or (d.isdigit() and 1200 <= int(d) < 1800):
        return C.YELLOW
    return C.RED

def platform_badge(platform):
    badges = {"cf": clr(" CF ", C.BOLD, C.BLUE),
              "ac": clr(" AC ", C.BOLD, C.CYAN),
              "lc": clr(" LC ", C.BOLD, C.YELLOW)}
    return badges.get(platform, platform.upper())

def draw_contest(elapsed, total, start_dt, end_dt,
                 problems, solve_status, solve_times, last_check, width):
    remaining = max(0, total - elapsed)
    ratio     = min(elapsed / total, 1.0) if total else 1.0

    if remaining <= 300:
        clk_col = (C.RED, C.BOLD)
    elif remaining <= 900:
        clk_col = (C.YELLOW, C.BOLD)
    else:
        clk_col = (C.WHITE, C.BOLD)

    inner_w = min(width - 4, 70)
    box_w   = inner_w + 4
    lpad    = max(0, (width - box_w) // 2)
    ind     = " " * lpad
    border  = clr("│", C.GREY)

    def hline(): return ind + clr("┌" + "─" * (box_w - 2) + "┐", C.GREY)
    def bline(): return ind + clr("└" + "─" * (box_w - 2) + "┘", C.GREY)
    def mline(): return ind + clr("├" + "─" * (box_w - 2) + "┤", C.GREY)

    def cline(s, raw=None):
        vis = raw if raw is not None else len(s)
        pad = inner_w - vis
        lp  = pad // 2
        rp  = pad - lp
        return ind + border + "  " + " " * lp + s + " " * rp + "  " + border

    def lline(s, raw=None):
        vis  = raw if raw is not None else len(s)
        rpad = inner_w - vis
        return ind + border + "  " + s + " " * rpad + "  " + border

    out = []
    out.append(hline())
    rem_s = fmt(remaining)
    out.append(cline(clr(rem_s, *clk_col), raw=len(rem_s)))

    sub = f"elapsed {fmt(elapsed)}  /  total {fmt(total)}"
    out.append(cline(clr(sub, C.GREY), raw=len(sub)))
    out.append(mline())

    bar = progress_bar(elapsed, total, inner_w)
    out.append(ind + border + "  " + bar + "  " + border)

    pct = f"{ratio*100:5.1f}%"
    out.append(cline(clr(pct, C.DIM), raw=len(pct)))
    out.append(mline())

    ts = f"started {start_dt.strftime('%H:%M:%S')}   ends {end_dt.strftime('%H:%M:%S')}"
    out.append(cline(clr(ts, C.GREY), raw=len(ts)))
    out.append(mline())

    solved_count = sum(1 for p in problems if solve_status.get(p["id"]))
    header = f"  PROBLEMS  {solved_count}/{len(problems)} solved"
    out.append(lline(clr(header, C.WHITE, C.BOLD), raw=len(header)))
    out.append(mline())

    for i, prob in enumerate(problems):
        pid      = prob["id"]
        is_done  = solve_status.get(pid, False)
        solved_t = solve_times.get(pid)

        glyph = clr("[+]", C.GREEN, C.BOLD) if is_done else clr("[ ]", C.GREY)
        badge = platform_badge(prob["platform"])

        if is_done and solved_t:
            right_str  = f"+{fmt(solved_t)}"
            right_disp = clr(right_str, C.GREEN)
            right_raw  = len(right_str)
        elif SHOW_DIFFICULTY:
            diff_str   = prob["difficulty"]
            right_str  = f"{diff_str:>6}"
            right_disp = clr(right_str, diff_colour(diff_str))
            right_raw  = len(right_str)
        else:
            right_str  = ""
            right_disp = ""
            right_raw  = 0

        fixed_raw  = 3 + 1 + 4 + 1
        right_slot = right_raw + (2 if right_raw else 0)
        max_title  = inner_w - fixed_raw - right_slot

        title_plain = prob["title"]
        if len(title_plain) > max_title:
            title_plain = title_plain[:max_title - 1] + "…"

        title_linked = hyperlink(prob["url"], title_plain)
        title_col    = C.GREEN if is_done else C.WHITE
        title_disp   = clr(title_linked, title_col)

        content_raw = len(title_plain)
        pad = max(0, inner_w - fixed_raw - content_raw - right_slot)

        line = (glyph + " " + badge + " " +
                title_disp +
                " " * pad +
                ("  " if right_raw else "") +
                right_disp)

        out.append(lline(line, raw=inner_w))

    out.append(mline())

    if last_check:
        age = int((datetime.now() - last_check).total_seconds())
        chk = f"last checked {age}s ago  |  polls every {CHECK_INTERVAL}s  |  Ctrl+C to quit"
    else:
        chk = f"waiting for first check...  |  Ctrl+C to quit"
    out.append(cline(clr(chk, C.GREY), raw=len(chk)))
    out.append(bline())

    return out

def draw_done(problems, solve_times, elapsed, total, width):
    inner_w = min(width - 4, 70)
    box_w   = inner_w + 4
    lpad    = max(0, (width - box_w) // 2)
    ind     = " " * lpad
    border  = clr("│", C.GREY)

    def hline(): return ind + clr("┌" + "─" * (box_w - 2) + "┐", C.GREY)
    def bline(): return ind + clr("└" + "─" * (box_w - 2) + "┘", C.GREY)
    def mline(): return ind + clr("├" + "─" * (box_w - 2) + "┤", C.GREY)
    def cline(s, raw=None):
        vis = raw if raw is not None else len(s)
        pad = inner_w - vis
        lp  = pad // 2; rp = pad - lp
        return ind + border + "  " + " " * lp + s + " " * rp + "  " + border
    def lline(s, raw=None):
        vis = raw if raw is not None else len(s)
        return ind + border + "  " + s + " " * max(0, inner_w - vis) + "  " + border

    solved_count = sum(1 for p in problems if solve_times.get(p["id"]) is not None)
    all_done     = solved_count == len(problems)

    lines = []
    lines.append(hline())
    msg     = "ALL PROBLEMS SOLVED" if all_done else "CONTEST OVER"
    msg_col = C.GREEN if all_done else C.RED
    lines.append(cline(clr(msg, msg_col, C.BOLD), raw=len(msg)))
    sub = f"{solved_count}/{len(problems)} solved  |  {fmt(elapsed)} elapsed"
    lines.append(cline(clr(sub, C.GREY), raw=len(sub)))
    lines.append(mline())

    if SHOW_DIFFICULTY:
        hdr = f"  {'#':>2}  {'Problem':<33}  {'Diff':>6}  {'Time':>10}"
    else:
        hdr = f"  {'#':>2}  {'Problem':<42}  {'Time':>10}"
    lines.append(lline(clr(hdr, C.WHITE, C.BOLD), raw=len(hdr)))
    lines.append(mline())

    for i, prob in enumerate(problems):
        pid    = prob["id"]
        st     = solve_times.get(pid)
        done   = st is not None
        t_str  = f"+{fmt(st)}" if done else "unsolved"
        t_col  = C.GREEN if done else C.GREY
        t_disp = clr(f"{t_str:>10}", t_col)

        if SHOW_DIFFICULTY:
            title = prob["title"]
            if len(title) > 33: title = title[:32] + "…"
            diff_disp = clr(f"{prob['difficulty']:>6}", diff_colour(prob["difficulty"]))
            title_link = hyperlink(prob["url"], title)
            title_disp = clr(title_link, C.WHITE if done else C.DIM)
            row_plain  = f"  {i+1:>2}  {title:<33}  "
            row_disp   = clr(f"  {i+1:>2}  ", C.WHITE if done else C.DIM) + title_disp + clr("  ", C.RESET)
            vis        = len(row_plain) + 6 + 2 + 10
            lines.append(lline(row_disp + diff_disp + clr("  ", C.RESET) + t_disp, raw=vis))
        else:
            title = prob["title"]
            if len(title) > 42: title = title[:41] + "…"
            title_link = hyperlink(prob["url"], title)
            title_disp = clr(title_link, C.WHITE if done else C.DIM)
            row_plain  = f"  {i+1:>2}  {title:<42}  "
            row_disp   = clr(f"  {i+1:>2}  ", C.WHITE if done else C.DIM) + title_disp + clr("  ", C.RESET)
            vis        = len(row_plain) + 10
            lines.append(lline(row_disp + t_disp, raw=vis))

    lines.append(bline())
    return lines