def sql_mode(self):
        sql_mode = self.mysql_server_data["sql_mode"]
        return set(sql_mode.split(",") if sql_mode else ())