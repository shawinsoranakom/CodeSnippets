def oracle_version(self):
        with self.temporary_connection():
            return tuple(int(x) for x in self.connection.version.split("."))