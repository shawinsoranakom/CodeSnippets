def __init__(self, data):
        self._store = {k.lower(): (k, v) for k, v in self._unpack_items(data)}