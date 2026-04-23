def __init__(self):
        self._lock = threading.Lock()
        self._state = ScriptRequestType.CONTINUE
        self._rerun_data = RerunData()