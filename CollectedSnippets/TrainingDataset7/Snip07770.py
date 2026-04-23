def __init__(self, *expressions, fillfactor=None, deduplicate_items=None, **kwargs):
        self.fillfactor = fillfactor
        self.deduplicate_items = deduplicate_items
        super().__init__(*expressions, **kwargs)