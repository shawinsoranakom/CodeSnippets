def test_get_constraints_unique_indexes_orders(self):
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(
                cursor,
                UniqueConstraintConditionModel._meta.db_table,
            )
        self.assertIn("cond_name_without_color_uniq", constraints)
        constraint = constraints["cond_name_without_color_uniq"]
        self.assertIs(constraint["unique"], True)
        self.assertEqual(constraint["columns"], ["name"])
        self.assertEqual(constraint["orders"], ["ASC"])