def __init__(self, *args, db_collation=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_collation = db_collation