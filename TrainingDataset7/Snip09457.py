def __str__(self):
        return self.create_index_name(self.table, self.columns, self.suffix)