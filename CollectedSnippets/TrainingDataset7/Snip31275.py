def assertIndexOrder(self, table, index, order):
        constraints = self.get_constraints(table)
        self.assertIn(index, constraints)
        index_orders = constraints[index]["orders"]
        self.assertTrue(
            all(val == expected for val, expected in zip(index_orders, order))
        )