def references_table(self, table):
        return super().references_table(table) or self.to_reference.references_table(
            table
        )