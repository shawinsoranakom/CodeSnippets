def references_column(self, table, column):
        return super().references_column(
            table, column
        ) or self.to_reference.references_column(table, column)