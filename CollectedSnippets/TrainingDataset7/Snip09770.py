def _collate_sql(self, collation, old_collation=None, table_name=None):
        if collation is None and old_collation is not None:
            collation = self._get_default_collation(table_name)
        return super()._collate_sql(collation, old_collation, table_name)