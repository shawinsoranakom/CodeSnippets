def get_connection_params(self):
        conn_params = self.settings_dict["OPTIONS"].copy()
        if "use_returning_into" in conn_params:
            del conn_params["use_returning_into"]
        return conn_params