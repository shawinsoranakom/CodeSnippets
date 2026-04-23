def __init__(self, *expressions, fillfactor=None, **kwargs):
        self.fillfactor = fillfactor
        super().__init__(*expressions, **kwargs)