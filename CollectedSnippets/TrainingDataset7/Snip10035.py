def __enter__(self):
        # Some SQLite schema alterations need foreign key constraints to be
        # disabled. Enforce it here for the duration of the schema edition.
        if not self.connection.disable_constraint_checking():
            raise NotSupportedError(
                "SQLite schema editor cannot be used while foreign key "
                "constraint checks are enabled. Make sure to disable them "
                "before entering a transaction.atomic() context because "
                "SQLite does not support disabling them in the middle of "
                "a multi-statement transaction."
            )
        return super().__enter__()