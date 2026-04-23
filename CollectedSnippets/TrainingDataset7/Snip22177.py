def test_db_loading(self):
        # Load db fixtures 1 and 2. These will load using the 'default'
        # database identifier implicitly.
        management.call_command("loaddata", "db_fixture_1", verbosity=0)
        management.call_command("loaddata", "db_fixture_2", verbosity=0)
        self.assertSequenceEqual(
            Article.objects.values_list("headline", flat=True),
            [
                "Who needs more than one database?",
                "Who needs to use compressed data?",
            ],
        )