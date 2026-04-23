def _collate_sql(self, collation, old_collation=None, table_name=None):
        return "COLLATE " + self.quote_name(collation) if collation else ""