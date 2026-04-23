def uses_server_side_binding(self):
        options = self.connection.settings_dict["OPTIONS"]
        return is_psycopg3 and options.get("server_side_binding") is True