def integer_field_range(self, internal_type):
        # SQLite doesn't enforce any integer constraints, but sqlite3 supports
        # integers up to 64 bits.
        if internal_type in [
            "PositiveBigIntegerField",
            "PositiveIntegerField",
            "PositiveSmallIntegerField",
        ]:
            return (0, 9223372036854775807)
        return (-9223372036854775808, 9223372036854775807)