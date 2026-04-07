def format_for_duration_arithmetic(self, sql):
        raise NotImplementedError(
            "subclasses of BaseDatabaseOperations may require a "
            "format_for_duration_arithmetic() method."
        )