def _clean_sql_mode():
            for alias in self.databases:
                if hasattr(connections[alias], "sql_mode"):
                    del connections[alias].sql_mode