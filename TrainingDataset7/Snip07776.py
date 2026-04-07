def __init__(self, *expressions, buffering=None, fillfactor=None, **kwargs):
        self.buffering = buffering
        self.fillfactor = fillfactor
        super().__init__(*expressions, **kwargs)