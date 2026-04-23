def assertConstraint(self, constraint_details, cols, unique=False, check=False):
        self.assertEqual(
            constraint_details,
            {
                "unique": unique,
                "columns": cols,
                "primary_key": False,
                "foreign_key": None,
                "check": check,
                "index": False,
            },
        )