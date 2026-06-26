# candidate

A CLI tool for competitive programmers to run timed virtual contests using problems from **Codeforces**, **AtCoder**, and **LeetCode**. Problems are pulled from your unsolved pool and tracked in real time as you submit.

---

## Some notable features

- **Virtual contests** on Codeforces, AtCoder, LeetCode, or a mixed set 
- Provides **tier-based problem selection**: 50% of problems are drawn from tier 1 (easier) and 50% from tier 2 (harder).
- The tool polls each platform and detects accepted submissions automatically; the contest ends as soon as all problems are solved.
- It will also auto-detect your session cookies, the tool reads your browser's stored session for AtCoder and LeetCode automatically (Chrome, Brave, Firefox, Safari, Edge, Opera are supported as of now, make sure you use one of these browsers)
- It supports **tag filtering** (`dp`, `graphs`). Not available in mixed (`x`) mode yet.
- You can adjust problems by **difficulty ranges and recency** via a `config.toml` file

---

## Requirements

- Python 3.11+
- For **LeetCode** and **AtCoder**: an account on the respective platform and at least one supported browser installed and logged in (Chrome, Brave, Firefox, Safari, Edge, or Opera)
- For **Codeforces**: only your handle is needed, no login required

---

## Configuration

Create a `config.toml` file in the project root (in the same directory as `config.example.toml`). Defaults are listed below.

```toml

# don't leave these empty

[handles]
codeforces = "your_cf_handle" 
atcoder    = "your_ac_handle" 
leetcode   = "your_lc_handle"

[codeforces]
tier1      = [1000, 1500]   # rating range for easier problems 
tier2      = [1600, 1900]   # rating range for harder problems
recent_max = 1900 # only include problems from contests >= given number

[atcoder]
tier1      = [1000, 1200]
tier2      = [1300, 1800]
recent_max = 320 # only include problems from ABC/ARC/AGC contests >= given number

[leetcode]
difficulties = ["MEDIUM", "HARD"] # valid values: "EASY", "MEDIUM", "HARD"
recent_max   = 2500  # only include problems with number >= given number

[display]
show_difficulties = false # show difficulty label next to each problem title
```

If a field is omitted, the following defaults apply:

|Key|Default|
|---|---|
|`handles.codeforces`|`""`|
|`handles.atcoder`|`""`|
|`handles.leetcode`|`""`|
|`codeforces.tier1`|`[1000, 1500]`|
|`codeforces.tier2`|`[1600, 1900]`|
|`codeforces.recent_max`|`1900`|
|`atcoder.tier1`|`[1000, 1200]`|
|`atcoder.tier2`|`[1300, 1800]`|
|`atcoder.recent_max`|`320`|
|`leetcode.difficulties`|`["MEDIUM", "HARD"]`|
|`leetcode.recent_max`|`2500`|
|`display.show_difficulties`|`false`|

You probably don't want to leave all handles empty. Enter at least one of them.

### `config.toml` options

**`[handles]`**: Your usernames on each platform. Used to filter out problems you've already solved and to check submissions during a contest.

**`[codeforces]`**

- `tier1` / `tier2`: Rating ranges that define the two difficulty buckets. The contest sampler draws 50% of problems from tier 1 and 50% from tier 2.
- `recent_max`: Filters the problem pool to only include problems from contests with an ID at or above this value.

**`[atcoder]`**

- `tier1` / `tier2`: Same as Codeforces but uses AtCoder's internal difficulty score.
- `recent_max`: Only problems from ABC/ARC/AGC contests numbered at or above this value are included.

**`[leetcode]`**

- `difficulties`: Which difficulty levels to include in the pool. The sampler treats lower difficulties as tier 1 and higher as tier 2.
- `recent_max`: Only problems with a frontend ID at or above this value are included.

**`[display]`**

- `show_difficulties`: When `true`, each problem in the contest view shows its difficulty rating or label next to the title. Note that this is OFF by default.

---

## Usage

Just run the tool and follow the interactive setup:

```
candidate
```

You will be prompted for:

|Prompt|Description|
|---|---|
|**Platform**|`cf` (Codeforces), `ac` (AtCoder), `lc` (LeetCode), `x` (mixed)|
|**Time limit**|Contest duration in minutes|
|**Number of problems**|How many problems to include|
|**Tags**|Optional comma-separated topic filters (e.g. `dp,graphs`). Not supported in mixed mode|

After setup, a preview of the selected problems is shown. Press **Enter** to start the contest or **Ctrl+C** to abort.

During the contest:

- The timer and solve status update every second.
- Submissions are checked against the platform every 30 seconds.
- The contest ends automatically when all problems are accepted, or when time runs out.
- Press **Ctrl+C** at any time to quit early.

---

## Session Cookies

AtCoder and LeetCode require an active session to fetch your submission history and verify solves. `candidate` auto-detects your session cookie from whichever supported browser you use. This requires you to be logged in on both platforms on any supported browser.

Detected cookies are cached in a `.env` file in the project root so subsequent runs are instant. If auto-detection fails (maybe you are not logged in, or the browser is unsupported), the tool will print a clear message explaining how to set the cookie manually in `.env`.

Supported browsers are: **Chrome**, **Brave**, **Firefox**, **Safari**, **Edge**, **Opera**

---

## Installation

### Recommended: `pipx` 

`pipx` installs CLI tools in isolated environments and puts them on your PATH automatically.

Install **pipx** if you don't have it:

```bash
# Linux/macOS
pip install --user pipx
pipx ensurepath

# Arch Linux
sudo pacman -S python-pipx

# macOS (Homebrew)
brew install pipx
```

Then install candidate:

```bash
pipx install candidate
```

To update later:
```bash
pipx upgrade candidate
```

---

### Alternative: `pip`

```bash
pip install candidate
pip install --user candidate
```

To update:
```bash
pip install --upgrade candidate
```


**If you don't have pip:**

```bash
# Linux/macOS
python3 -m ensurepip --upgrade

# Arch Linux
sudo pacman -S python-pip

# Ubuntu/Debian
sudo apt install python3-pip

# macOS (Homebrew)
brew install python
```
---

### First Run

Run the tool once to generate a default config file:

```bash
candidate
```

On first launch, if no config is found, the tool will create one at:

```~/.config/candidate/config.toml```

Open it and fill in your handles, and make any other changes if you want.

Then run `candidate` again.

---

### Session Cookies (For AtCoder and LeetCode)

As long as you are logged in to AtCoder or LeetCode in a supported browser, `candidate` will detect your session automatically on first run and cache it for future runs.

If auto-detection fails, you can set cookies manually in `~/.config/candidate/.env`:

```
LC_SESSION_COOKIE=your_leetcode_session_here  
AC_SESSION_COOKIE=your_atcoder_session_here
```

After you add the session keys, you can proceed safely.