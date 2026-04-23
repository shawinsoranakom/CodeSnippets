def supports_transactions(self):
        """
        All storage engines except MyISAM support transactions.
        """
        return self._mysql_storage_engine != "MyISAM"