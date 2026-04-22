def __init__(self, state: SessionState):
        self._state = state
        # TODO: we'd prefer this be a threading.Lock instead of RLock -
        #  but `call_callbacks` first needs to be rewritten.
        self._lock = threading.RLock()
        self._disconnected = False