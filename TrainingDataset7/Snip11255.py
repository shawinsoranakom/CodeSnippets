def cached_col(self):
        return ColPairs(self.model._meta.db_table, self.fields, self.fields, self)