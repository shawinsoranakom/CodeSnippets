def _mysql_storage_engine(self):
        """
        Internal method used in Django tests. Don't rely on this from your code
        """
        return self.connection.mysql_server_data["default_storage_engine"]