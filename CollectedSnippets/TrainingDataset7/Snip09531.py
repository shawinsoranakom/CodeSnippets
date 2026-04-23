def supports_index_column_ordering(self):
        if self._mysql_storage_engine != "InnoDB":
            return False
        return True