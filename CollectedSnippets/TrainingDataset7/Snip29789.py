def test_key_sql_injection(self):
        with CaptureQueriesContext(connection) as queries:
            self.assertFalse(
                HStoreModel.objects.filter(
                    **{
                        "field__test' = 'a') OR 1 = 1 OR ('d": "x",
                    }
                ).exists()
            )
        self.assertIn(
            """."field" -> 'test'' = ''a'') OR 1 = 1 OR (''d') = 'x' """,
            queries[0]["sql"],
        )