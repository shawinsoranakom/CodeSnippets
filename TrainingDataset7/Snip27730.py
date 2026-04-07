def test_sorted_imports(self):
        """
        #24155 - Tests ordering of imports.
        """
        migration = type(
            "Migration",
            (migrations.Migration,),
            {
                "operations": [
                    migrations.AddField(
                        "mymodel",
                        "myfield",
                        models.DateTimeField(
                            default=datetime.datetime(
                                2012, 1, 1, 1, 1, tzinfo=datetime.UTC
                            ),
                        ),
                    ),
                    migrations.AddField(
                        "mymodel",
                        "myfield2",
                        models.FloatField(default=time.time),
                    ),
                ]
            },
        )
        writer = MigrationWriter(migration)
        output = writer.as_string()
        self.assertIn(
            "import datetime\nimport time\nfrom django.db import migrations, models\n",
            output,
        )