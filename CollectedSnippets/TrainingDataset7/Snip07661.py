def cast_db_type(self, connection):
        size = self.size or ""
        return "%s[%s]" % (self.base_field.cast_db_type(connection), size)