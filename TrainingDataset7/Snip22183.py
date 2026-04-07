def test_unmatched_identifier_loading(self):
        # Db fixture 3 won't load because the database identifier doesn't
        # match.
        with self.assertRaisesMessage(
            CommandError, "No fixture named 'db_fixture_3' found."
        ):
            management.call_command("loaddata", "db_fixture_3", verbosity=0)
        with self.assertRaisesMessage(
            CommandError, "No fixture named 'db_fixture_3' found."
        ):
            management.call_command(
                "loaddata", "db_fixture_3", verbosity=0, database="default"
            )
        self.assertQuerySetEqual(Article.objects.all(), [])