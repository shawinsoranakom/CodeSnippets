def bare_select_suffix(self):
        return "" if self.connection.oracle_version >= (23,) else " FROM DUAL"