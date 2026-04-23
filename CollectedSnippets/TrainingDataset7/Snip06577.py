def supports_spatial_index(self, cursor, table_name):
        # Supported with MyISAM, Aria, or InnoDB.
        storage_engine = self.get_storage_engine(cursor, table_name)
        return storage_engine in ("MyISAM", "Aria", "InnoDB")