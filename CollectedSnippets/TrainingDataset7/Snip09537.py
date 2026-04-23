def supports_uuid7_function(self):
        if self.connection.mysql_is_mariadb:
            return self.connection.mysql_version >= (11, 7)
        return False