def test_loading_using(self):
        # Load fixtures 1 and 2. These will load using the 'default' database
        # identifier explicitly.
        management.call_command(
            "loaddata", "db_fixture_1", verbosity=0, database="default"
        )
        management.call_command(
            "loaddata", "db_fixture_2", verbosity=0, database="default"
        )
        self.assertSequenceEqual(
            Article.objects.values_list("headline", flat=True),
            [
                "Who needs more than one database?",
                "Who needs to use compressed data?",
            ],
        )