def __init__(
        self, *expressions, fastupdate=None, gin_pending_list_limit=None, **kwargs
    ):
        self.fastupdate = fastupdate
        self.gin_pending_list_limit = gin_pending_list_limit
        super().__init__(*expressions, **kwargs)