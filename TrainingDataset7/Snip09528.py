def ignores_table_name_case(self):
        return self.connection.mysql_server_data["lower_case_table_names"]