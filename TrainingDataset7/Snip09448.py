def references_index(self, table, index):
        return self.references_table(table) and str(self) == index