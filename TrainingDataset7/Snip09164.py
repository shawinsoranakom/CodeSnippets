def init_connection_state(self):
        """Initialize the database connection settings."""
        if self.alias not in RAN_DB_VERSION_CHECK:
            self.check_database_version_supported()
            RAN_DB_VERSION_CHECK.add(self.alias)