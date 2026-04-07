def test_disable_constraint_checking_failure_disallowed(self):
        """
        SQLite schema editor is not usable within an outer transaction if
        foreign key constraint checks are not disabled beforehand.
        """
        msg = (
            "SQLite schema editor cannot be used while foreign key "
            "constraint checks are enabled. Make sure to disable them "
            "before entering a transaction.atomic() context because "
            "SQLite does not support disabling them in the middle of "
            "a multi-statement transaction."
        )
        with self.assertRaisesMessage(NotSupportedError, msg):
            with transaction.atomic(), connection.schema_editor(atomic=True):
                pass