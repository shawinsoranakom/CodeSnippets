def mysql_is_mariadb(self):
        return "mariadb" in self.mysql_server_info.lower()