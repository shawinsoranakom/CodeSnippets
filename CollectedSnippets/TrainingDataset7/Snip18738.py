def test_autoincrement(self):
        """
        auto_increment fields are created with the AUTOINCREMENT keyword
        in order to be monotonically increasing (#10164).
        """
        with connection.schema_editor(collect_sql=True) as editor:
            editor.create_model(Square)
            statements = editor.collected_sql
        match = re.search('"id" ([^,]+),', statements[0])
        self.assertIsNotNone(match)
        self.assertEqual(
            "integer NOT NULL PRIMARY KEY AUTOINCREMENT",
            match[1],
            "Wrong SQL used to create an auto-increment column on SQLite",
        )