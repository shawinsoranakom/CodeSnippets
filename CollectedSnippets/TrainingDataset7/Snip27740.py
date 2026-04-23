def test_run_before(self):
        for run_before, expected_run_before_str in [
            ([("foo", "0001_bar")], "    run_before = [('foo', '0001_bar')]\n"),
            (
                [("foo", "0001_bar"), ("foo", "0002_baz")],
                "    run_before = [('foo', '0001_bar'), ('foo', '0002_baz')]\n",
            ),
        ]:
            with self.subTest(run_before=run_before):
                migration = type(
                    "Migration",
                    (migrations.Migration,),
                    {"operations": [], "run_before": run_before},
                )
                writer = MigrationWriter(migration)
                output = writer.as_string()
                self.assertIn(expected_run_before_str, output)