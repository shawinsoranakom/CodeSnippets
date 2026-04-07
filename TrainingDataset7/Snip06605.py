def __str__(self):
        return "%s - %s (SRID: %s)" % (self.table_name, self.column_name, self.srid)