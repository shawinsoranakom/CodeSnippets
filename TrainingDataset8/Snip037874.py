def __init__(self, msg: ForwardMsg):
            self.msg = msg
            self._session_script_run_counts: MutableMapping[
                "AppSession", int
            ] = WeakKeyDictionary()