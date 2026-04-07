def test_constraint_checks_disabled_atomic_allowed(self):
        """
        SQLite schema editor is usable within an outer transaction as long as
        foreign key constraints checks are disabled beforehand.
        """

        def constraint_checks_enabled():
            with connection.cursor() as cursor:
                return bool(cursor.execute("PRAGMA foreign_keys").fetchone()[0])

        with connection.constraint_checks_disabled(), transaction.atomic():
            with connection.schema_editor(atomic=True):
                self.assertFalse(constraint_checks_enabled())
            self.assertFalse(constraint_checks_enabled())
        self.assertTrue(constraint_checks_enabled())