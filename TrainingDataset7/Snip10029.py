def insert_statement(self, on_conflict=None):
        if on_conflict == OnConflict.IGNORE:
            return "INSERT OR IGNORE INTO"
        return super().insert_statement(on_conflict=on_conflict)