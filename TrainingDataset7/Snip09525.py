def has_select_for_update_of(self):
        return not self.connection.mysql_is_mariadb