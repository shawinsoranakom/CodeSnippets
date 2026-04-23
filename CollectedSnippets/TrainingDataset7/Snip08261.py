def __init__(self, dir, params):
        super().__init__(params)
        self._dir = os.path.abspath(dir)
        self._createdir()