def __init__(self, backends=None):
        # backends is an optional dict of storage backend definitions
        # (structured like settings.STORAGES).
        self._backends = backends
        self._storages = {}