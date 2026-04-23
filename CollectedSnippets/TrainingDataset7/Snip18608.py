def test_quote_name_db_table(self):
        model = VeryLongModelNameZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ
        db_table = model._meta.db_table.upper()
        self.assertEqual(
            f'"{db_table}"',
            connection.ops.quote_name(
                "backends_verylongmodelnamezzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",
            ),
        )