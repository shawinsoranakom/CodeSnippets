def get_new_connection(self, conn_params):
        if self.pool:
            return self.pool.acquire()
        return Database.connect(
            user=self.settings_dict["USER"],
            password=self.settings_dict["PASSWORD"],
            dsn=dsn(self.settings_dict),
            **conn_params,
        )