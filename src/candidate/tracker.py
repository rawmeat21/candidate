import threading
from datetime import datetime
from .checkers import check_solved
from .config import CHECK_INTERVAL

class SolveTracker:
    def __init__(self, problems, start_dt):
        self.problems    = problems
        self.start_dt    = start_dt
        self.status      = {p["id"]: False for p in problems}
        self.solve_times = {}
        self.last_check  = None
        self._lock       = threading.Lock()
        self._stop       = threading.Event()

    def start(self):
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        self._do_check()
        while not self._stop.is_set():
            slept = 0
            while slept < CHECK_INTERVAL and not self._stop.is_set():
                self._stop.wait(1)
                slept += 1
            if not self._stop.is_set():
                self._do_check()

    def _do_check(self):
        check_started = datetime.now()
        with self._lock:
            self.last_check = check_started
        try:
            fresh   = check_solved(self.problems)
            elapsed = (datetime.now() - self.start_dt).total_seconds()
            with self._lock:
                for pid, solved in fresh.items():
                    if solved and not self.status[pid]:
                        self.solve_times[pid] = elapsed
                    self.status[pid] = solved
        except Exception:
            pass

    def snapshot(self):
        with self._lock:
            return dict(self.status), dict(self.solve_times), self.last_check

    def all_solved(self):
        with self._lock:
            return all(self.status.values())