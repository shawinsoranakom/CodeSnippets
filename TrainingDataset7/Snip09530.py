def can_introspect_json_field(self):
        if self.connection.mysql_is_mariadb:
            return self.can_introspect_check_constraints
        return True