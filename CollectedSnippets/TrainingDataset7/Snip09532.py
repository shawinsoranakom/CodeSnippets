def supports_expression_indexes(self):
        return (
            not self.connection.mysql_is_mariadb
            and self._mysql_storage_engine != "MyISAM"
        )