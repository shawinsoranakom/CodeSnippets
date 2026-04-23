def is_sql_auto_is_null_enabled(self):
        return self.connection.mysql_server_data["sql_auto_is_null"]