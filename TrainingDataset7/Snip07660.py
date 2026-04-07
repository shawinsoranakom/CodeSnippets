def db_type(self, connection):
        size = self.size or ""
        return "%s[%s]" % (self.base_field.db_type(connection), size)