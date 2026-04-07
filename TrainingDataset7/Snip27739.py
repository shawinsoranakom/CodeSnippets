def test_composite_pk_import(self):
        migration = type(
            "Migration",
            (migrations.Migration,),
            {
                "operations": [
                    migrations.AddField(
                        "foo",
                        "bar",
                        models.CompositePrimaryKey("foo_id", "bar_id"),
                    ),
                ],
            },
        )
        writer = MigrationWriter(migration)
        output = writer.as_string()
        self.assertEqual(output.count("import"), 1)
        self.assertIn("from django.db import migrations, models", output)