def minimum_database_version(self):
        if self.connection.mysql_is_mariadb:
            return (10, 11)
        else:
            return (8, 4)