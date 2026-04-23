def test_postgres_options(self):
        qs = Tag.objects.filter(name="test")
        test_options = [
            {"COSTS": False, "BUFFERS": True, "ANALYZE": True},
            {"costs": False, "buffers": True, "analyze": True},
            {"verbose": True, "timing": True, "analyze": True},
            {"verbose": False, "timing": False, "analyze": True},
            {"summary": True},
            {"settings": True},
            {"analyze": True, "wal": True},
        ]
        if connection.features.is_postgresql_16:
            test_options.append({"generic_plan": True})
        if connection.features.is_postgresql_17:
            test_options.append({"memory": True})
            test_options.append({"serialize": "TEXT", "analyze": True})
            test_options.append({"serialize": "text", "analyze": True})
            test_options.append({"serialize": "BINARY", "analyze": True})
            test_options.append({"serialize": "binary", "analyze": True})
        for options in test_options:
            with self.subTest(**options), transaction.atomic():
                with CaptureQueriesContext(connection) as captured_queries:
                    qs.explain(format="text", **options)
                self.assertEqual(len(captured_queries), 1)
                for name, value in options.items():
                    if isinstance(value, str):
                        option = "{} {}".format(name.upper(), value.upper())
                    else:
                        option = "{} {}".format(
                            name.upper(), "true" if value else "false"
                        )
                    self.assertIn(option, captured_queries[0]["sql"])