def supports_geometry_field_unique_index(self):
        # Not supported in MySQL since
        # https://dev.mysql.com/worklog/task/?id=11808
        return self.connection.mysql_is_mariadb