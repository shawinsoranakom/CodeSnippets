def init_connection_state(self):
        super().init_connection_state()

        if self.connection is not None and not self.pool:
            commit = self._configure_connection(self.connection)

            if commit and not self.get_autocommit():
                self.connection.commit()