def test_loaddata_app_option(self):
        with self.assertRaisesMessage(
            CommandError, "No fixture named 'db_fixture_1' found."
        ):
            management.call_command(
                "loaddata", "db_fixture_1", verbosity=0, app_label="someotherapp"
            )
        self.assertQuerySetEqual(Article.objects.all(), [])
        management.call_command(
            "loaddata", "db_fixture_1", verbosity=0, app_label="fixtures"
        )
        self.assertEqual(
            Article.objects.get().headline,
            "Who needs more than one database?",
        )