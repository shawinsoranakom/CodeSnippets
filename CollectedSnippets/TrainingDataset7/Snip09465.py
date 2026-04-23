def __str__(self):
        suffix = self.suffix_template % {
            "to_table": self.to_reference.table,
            "to_column": self.to_reference.columns[0],
        }
        return self.create_fk_name(self.table, self.columns, suffix)