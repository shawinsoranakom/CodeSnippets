def setUp(self):
        self.reference = Columns(
            "table", ["first_column", "second_column"], lambda column: column.upper()
        )