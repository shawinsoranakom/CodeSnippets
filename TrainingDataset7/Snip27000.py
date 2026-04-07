def assertConstraintExists(self, table, name, value=True, using="default"):
        with connections[using].cursor() as cursor:
            constraints = (
                connections[using].introspection.get_constraints(cursor, table).items()
            )
            self.assertEqual(
                value,
                any(c["check"] for n, c in constraints if n == name),
            )