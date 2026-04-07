def assertIndexNotExists(self, table, columns):
        return self.assertIndexExists(table, columns, False)