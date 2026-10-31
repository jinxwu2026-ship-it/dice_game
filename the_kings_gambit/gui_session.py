"""Connect blocking game controllers to a responsive window using two queues.

The worker owns game state. The window receives copies and submits one command
per input request; pygame is only used by the main thread in gui.py.
"""

from copy import deepcopy
from queue import Empty, Queue
from threading import Event, Lock, Thread

from the_kings_gambit.battle import run_match, run_practice
from the_kings_gambit.main import play_logged
from the_kings_gambit.progression import run_campaign


class WindowBridge:
    def __init__(self):
        self.events = Queue()
        self.commands = Queue()
        self.stopped = Event()
        self.lock = Lock()
        self.request = 0
        self.pending = None
        self.view = None
        self.resources = dict(hp=None, coins=None, stage=None)

    def __call__(self, text):
        # Structured views replace terminal frames, never parse ASCII output.
        pass

    def present(self, screen, **data):
        run = data.get("run")
        if run is not None:
            self.resources = dict(hp=run.hp, coins=run.coins, stage=run.encounter_index+1)
        self.view = deepcopy(dict(screen=screen, resources=self.resources, **data))
        self.events.put(dict(kind="view", view=self.view))

    def read(self, prompt):
        with self.lock:
            self.request += 1
            token = self.request
            self.pending = token
        self.events.put(dict(kind="input", view=self.view, token=token))
        while not self.stopped.is_set():
            try:
                submitted, command = self.commands.get(timeout=0.1)
            except Empty:
                continue
            if submitted == token:
                return command
        return "q"

    def submit(self, token, command):
        with self.lock:
            if token is None or token != self.pending or self.stopped.is_set():
                return False
            self.pending = None
        self.commands.put((token, command))
        return True

    def pause(self, seconds):
        if self.stopped.wait(seconds):
            raise KeyboardInterrupt

    def close(self):
        self.stopped.set()


class GameSession:
    def __init__(self, mode, *, ai_delay=2, score_ambition=500, random_source=None,
                 log_games=True, target=2000):
        if mode not in ("run", "practice", "match"):
            raise ValueError("unknown window game mode")
        self.mode = mode
        self.bridge = WindowBridge()
        self.options = dict(input_func=self.bridge.read, output_func=self.bridge,
                            random_source=random_source)
        if mode != "practice":
            self.options.update(ai_delay=ai_delay, score_ambition=score_ambition,
                                sleep_func=self.bridge.pause, target=target)
        self.log_games = log_games
        self.thread = Thread(target=self._play, name="dice-game")

    def start(self):
        self.thread.start()

    def _play(self):
        try:
            path = None
            if self.mode == "practice":
                result = run_practice(**self.options)
            elif self.log_games:
                result, path = play_logged(self.mode, **self.options)
            else:
                play = run_campaign if self.mode == "run" else run_match
                result = play(**self.options)
            self.bridge.events.put(dict(kind="finished", result=deepcopy(result), log_path=path))
        except Exception as error:
            self.bridge.events.put(dict(kind="error", message=f"{type(error).__name__}: {error}"))

    def close(self):
        self.bridge.close()
