import random
from .network import req
from . import config
import re
import requests

def cf_fetch_problems(tags=None):
    solved_data = req(f"https://codeforces.com/api/user.status?handle={config.CF_HANDLE}&from=1&count=10000")
    solved = set()
    if solved_data and solved_data.get("status") == "OK":
        for s in solved_data["result"]:
            if s.get("verdict") == "OK" and "contestId" in s["problem"]:
                solved.add(f"{s['problem']['contestId']}-{s['problem']['index']}")

    pool_data = req("https://codeforces.com/api/problemset.problems")
    if not pool_data or pool_data.get("status") != "OK":
        return [], []

    t1, t2 = [], []
    for p in pool_data["result"]["problems"]:
        if p.get("contestId", 0) < config.CF_RECENT:
            continue
        rating = p.get("rating")
        if rating is None:
            continue
        pid = f"{p['contestId']}-{p['index']}"
        if pid in solved:
            continue
        if tags and not set(tags).intersection(set(p.get("tags", []))):
            continue
        entry = {
            "id":         pid,
            "title":      f"{p['contestId']}{p['index']} - {p['name']}",
            "url":        f"https://codeforces.com/problemset/problem/{p['contestId']}/{p['index']}",
            "difficulty": str(rating),
            "platform":   "cf",
        }
        if config.CF_T1[0] <= rating <= config.CF_T1[1]:
            t1.append(entry)
        elif config.CF_T2[0] <= rating <= config.CF_T2[1]:
            t2.append(entry)
    return t1, t2

def ac_fetch_problems(tags=None):

    # will return a list of problems respecting specified rating and problem recent-ness

    hdrs = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0"}

    # getting all submissions
    solved_data = req(
        f"https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions?user={config.AC_HANDLE}&from_second=0",
        headers=hdrs,
    )

    solved = set() # store solved problem ids

    if solved_data:
        solved = {s["problem_id"] for s in solved_data if s.get("result") == "AC"}
    try:
        # this won't work, atcoder doesn't allow viewing submissions so ignore this
        live_url = f"https://atcoder.jp/submissions?f.User={config.AC_HANDLE}&f.Status=AC"

        r = requests.get(live_url, headers=hdrs, timeout=10)
        if r.status_code == 200:
            live_solved = re.findall(r"/contests/[^/]+/tasks/([a-zA-Z0-9_]+)", r.text)
            solved.update(live_solved)
    except Exception:
        pass


    probs  = req("https://kenkoooo.com/atcoder/resources/problems.json",       headers=hdrs) # for problems
    models = req("https://kenkoooo.com/atcoder/resources/problem-models.json", headers=hdrs) # for rating of problems

    if not probs or not models:
        return [], []

    t1, t2 = [], []
    for p in probs:
        pid = p["id"]
        if pid in solved:
            continue
        parts = pid.split("_")

        if parts and parts[0][:3] in ("abc", "arc", "agc"):
            try:
                if int(parts[0][3:]) < config.AC_RECENT:
                    continue
            except ValueError:
                continue
        else: 
            continue

        model = models.get(pid)
        if not model or model.get("difficulty") is None:
            continue
        diff = model["difficulty"]

        # our problem entry
        entry = {
            "id":         pid,
            "title":      p["title"],
            "url":        f"https://atcoder.jp/contests/{p['contest_id']}/tasks/{pid}",
            "difficulty": f"{diff:.0f}",
            "platform":   "ac",
        }

        if config.AC_T1[0] <= diff <= config.AC_T1[1]:
            t1.append(entry)
        elif config.AC_T2[0] <= diff <= config.AC_T2[1]:
            t2.append(entry)
    return t1, t2

def lc_fetch_problems(tags=None):
    hdrs = {
        "content-type": "application/json",
        "cookie": f"LEETCODE_SESSION={config.LC_SESSION_COOKIE}",
    }
    query = """
    query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
      problemsetQuestionList: questionList(categorySlug: $categorySlug, limit: $limit, skip: $skip, filters: $filters) {
        data { questionFrontendId title titleSlug difficulty status topicTags { slug } }
      }
    }
    """
    questions  = []
    lc_solved  = set()
    for page in range(30):
        variables = {
            "categorySlug": "",
            "skip": page * 100,
            "limit": 100,
            "filters": {"orderBy": "FRONTEND_ID", "sortOrder": "DESCENDING", "premiumOnly": False},
        }
        data = req("https://leetcode.com/graphql", method="POST",
                    headers=hdrs, json_data={"query": query, "variables": variables})
        if not data or "errors" in data:
            break
        batch = data["data"]["problemsetQuestionList"]["data"]
        if not batch:
            break
        for q in batch:
            if q.get("status") == "ac":
                lc_solved.add(q["titleSlug"])
        questions.extend(batch)
        try:
            if batch and int(batch[-1]["questionFrontendId"]) < config.LC_RECENT:
                break
        except (ValueError, KeyError):
            pass

    allowed = {d.upper() for d in config.LC_DIFFICULTIES}
    pool = []
    for q in questions:
        if q["titleSlug"] in lc_solved:
            continue
        if q.get("status") == "ac":
            continue
        try:
            if int(q["questionFrontendId"]) < config.LC_RECENT:
                continue
        except ValueError:
            continue
        if q["difficulty"].upper() not in allowed:
            continue
        if tags:
            problem_tags = {t["slug"] for t in q.get("topicTags", [])}
            if not set(tags).intersection(problem_tags):
                continue
        pool.append({
            "id":         q["titleSlug"],
            "title":      f"{q['questionFrontendId']}. {q['title']}",
            "url":        f"https://leetcode.com/problems/{q['titleSlug']}/",
            "difficulty": q["difficulty"],
            "platform":   "lc",
        })

    difficulty_rank = {"EASY": 0, "MEDIUM": 1, "HARD": 2}
    sorted_diffs    = sorted(allowed, key=lambda d: difficulty_rank.get(d, 1))
    mid             = len(sorted_diffs) // 2

    t1_diffs = set(sorted_diffs[:max(1, mid)])
    t2_diffs = set(sorted_diffs[max(1, mid):])
    if not t2_diffs:
        t2_diffs = t1_diffs
        t1_diffs = set()

    t1 = [p for p in pool if p["difficulty"].upper() in t1_diffs]
    t2 = [p for p in pool if p["difficulty"].upper() in t2_diffs]
    return t1, t2

def mixed_fetch_problems(tags=None):
    t1, t2 = [], []
    for fn in (lc_fetch_problems, cf_fetch_problems):
        a, b = fn(tags)
        t1 += a
        t2 += b
    return t1, t2

def sample_problems(t1, t2, total):

    # get 'total' number of problems

    t2_q = round(total * 0.5) # adjust to change difficulty of later problems
    t1_q = total - t2_q

    sel2 = random.sample(t2, min(t2_q, len(t2)))

    t1_q += max(0, t2_q - len(sel2))

    sel1 = random.sample(t1, min(t1_q, len(t1)))

    rem  = total - len(sel1) - len(sel2)
    if rem > 0:
        extra_pool = [p for p in t2 if p not in sel2]
        sel2 += random.sample(extra_pool, min(rem, len(extra_pool)))
    return sel1 + sel2