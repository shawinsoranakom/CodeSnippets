def test_atomic_is_false(self):
        migration = type(
            "Migration",
            (migrations.Migration,),
            {"operations": [], "atomic": False},
        )
        writer = MigrationWriter(migration)
        output = writer.as_string()
        self.assertIn("    atomic = False\n", output)