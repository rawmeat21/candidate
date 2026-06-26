import time
import re
import requests
from .network import req
from . import config
import os
from dotenv import load_dotenv
from pathlib import Path
from .config import *

def _cf_solved_set():
    data = req(f"https://codeforces.com/api/user.status?handle={config.CF_HANDLE}&from=1&count=15")
    if not data or data.get("status") != "OK":
        return set()
    return {
        f"{s['problem']['contestId']}-{s['problem']['index']}"
        for s in data["result"]
        if s.get("verdict") == "OK" and "contestId" in s["problem"]
    }

def _ac_solved_set(problems):
    """
    Queries AtCoder's personal submission list page per active contest, filtered by AC.
    Fires exactly one request per contest and safely isolates the table rows.
    """
    solved = set()

    contest_ids = set()
    for p in problems:
        if p.get("platform") == "ac":

            parts = p["url"].split("/")
            if len(parts) >= 5:
                contest_ids.add(parts[4])

    hdrs = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0"
    }
    cookies = {"REVEL_SESSION": AC_SESSION_COOKIE}

    # print(contest_ids)
    # with open("output.txt", "w", encoding="utf-8") as file:
    #     file.write("\n".join(str(item) for item in contest_ids))

    for contest_id in contest_ids:

        url = f"https://atcoder.jp/contests/{contest_id}/submissions/me?f.Status=AC"
        try:
            r = requests.get(url, headers=hdrs, cookies=cookies, timeout=6)
            if r.status_code == 200:
                # print(r.text)
                # with open("out.txt", "w", encoding="utf-8") as file:
                #     file.write(r.text)
                table_match = re.search(r'<table[^>]*>([\s\S]*?)</table>', r.text)
                if table_match:
                    table_html = table_match.group(1)

                    pids = re.findall(r'/tasks/([a-zA-Z0-9_]+)', table_html)
                    solved.update(pids)
        except Exception:
            pass  

    # print(solved)
    return solved

def _lc_solved_set():
    hdrs = {
        "content-type": "application/json",
        "cookie": f"LEETCODE_SESSION={LC_SESSION_COOKIE}",
        "referer": "https://leetcode.com",
        "x-csrftoken": "dummy",
    }
    q_recent = """
    query recentAcSubmissions($username: String!, $limit: Int!) {
      recentAcSubmissionList(username: $username, limit: $limit) {
        titleSlug
      }
    }
    """
    data = req("https://leetcode.com/graphql", method="POST",
                headers=hdrs,
                json_data={"query": q_recent, "variables": {"username": config.LC_HANDLE, "limit": 15}})

    solved = set()
    if data and not data.get("errors"):
        for item in (data["data"].get("recentAcSubmissionList") or []):
            solved.add(item["titleSlug"])
    return solved

def check_solved(problems):
    platforms = {p["platform"] for p in problems}
    solved_sets = {}
    
    if "cf" in platforms:
        solved_sets["cf"] = _cf_solved_set()
    if "ac" in platforms:
        ac_probs = [p for p in problems if p["platform"] == "ac"]
        solved_sets["ac"] = _ac_solved_set(ac_probs)
    if "lc" in platforms:
        solved_sets["lc"] = _lc_solved_set()

    result = {}
    for p in problems:
        result[p["id"]] = p["id"] in solved_sets.get(p["platform"], set())
    return result


