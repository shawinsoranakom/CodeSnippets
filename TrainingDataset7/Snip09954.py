def get_new_connection(self, conn_params):
        conn = Database.connect(**conn_params)
        register_functions(conn)

        conn.execute("PRAGMA foreign_keys = ON")
        # The macOS bundled SQLite defaults legacy_alter_table ON, which
        # prevents atomic table renames.
        conn.execute("PRAGMA legacy_alter_table = OFF")
        for init_command in self.init_commands:
            if init_command := init_command.strip():
                conn.execute(init_command)
        return conn