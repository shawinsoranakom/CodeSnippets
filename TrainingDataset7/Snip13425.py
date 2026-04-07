def __init__(self, msg, tried=None, backend=None, chain=None):
        self.backend = backend
        if tried is None:
            tried = []
        self.tried = tried
        if chain is None:
            chain = []
        self.chain = chain
        super().__init__(msg)