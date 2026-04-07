def get_db_converters(self, connection):
        if hasattr(self, "from_db_value"):
            return [self.from_db_value]
        return []