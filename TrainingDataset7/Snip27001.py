def assertConstraintNotExists(self, table, name):
        return self.assertConstraintExists(table, name, False)