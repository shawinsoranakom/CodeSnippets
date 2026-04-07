def test_sorted_dependencies(self):
        migration = type(
            "Migration",
            (migrations.Migration,),
            {
                "operations": [
                    migrations.AddField("mymodel", "myfield", models.IntegerField()),
                ],
                "dependencies": [
                    ("testapp10", "0005_fifth"),
                    ("testapp02", "0005_third"),
                    ("testapp02", "0004_sixth"),
                    ("testapp01", "0001_initial"),
                ],
            },
        )
        output = MigrationWriter(migration, include_header=False).as_string()
        self.assertIn(
            "    dependencies = [\n"
            "        ('testapp01', '0001_initial'),\n"
            "        ('testapp02', '0004_sixth'),\n"
            "        ('testapp02', '0005_third'),\n"
            "        ('testapp10', '0005_fifth'),\n"
            "    ]",
            output,
        )