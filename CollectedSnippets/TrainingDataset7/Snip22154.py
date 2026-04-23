def test_dumpdata_with_excludes(self):
        # Load fixture1 which has a site, two articles, and a category
        Site.objects.all().delete()
        management.call_command("loaddata", "fixture1.json", verbosity=0)

        # Excluding fixtures app should only leave sites
        self._dumpdata_assert(
            ["sites", "fixtures"],
            '[{"pk": 1, "model": "sites.site", "fields": '
            '{"domain": "example.com", "name": "example.com"}}]',
            exclude_list=["fixtures"],
        )

        # Excluding fixtures.Article/Book should leave fixtures.Category
        self._dumpdata_assert(
            ["sites", "fixtures"],
            '[{"pk": 1, "model": "sites.site", '
            '"fields": {"domain": "example.com", "name": "example.com"}}, '
            '{"pk": 1, "model": "fixtures.category", "fields": '
            '{"description": "Latest news stories", "title": "News Stories"}}]',
            exclude_list=["fixtures.Article", "fixtures.Book"],
        )

        # Excluding fixtures and fixtures.Article/Book should be a no-op
        self._dumpdata_assert(
            ["sites", "fixtures"],
            '[{"pk": 1, "model": "sites.site", '
            '"fields": {"domain": "example.com", "name": "example.com"}}, '
            '{"pk": 1, "model": "fixtures.category", '
            '"fields": {"description": "Latest news stories", '
            '"title": "News Stories"}}]',
            exclude_list=["fixtures.Article", "fixtures.Book"],
        )

        # Excluding sites and fixtures.Article/Book should only leave
        # fixtures.Category
        self._dumpdata_assert(
            ["sites", "fixtures"],
            '[{"pk": 1, "model": "fixtures.category", "fields": '
            '{"description": "Latest news stories", "title": "News Stories"}}]',
            exclude_list=["fixtures.Article", "fixtures.Book", "sites"],
        )

        # Excluding a bogus app should throw an error
        with self.assertRaisesMessage(
            management.CommandError, "No installed app with label 'foo_app'."
        ):
            self._dumpdata_assert(["fixtures", "sites"], "", exclude_list=["foo_app"])

        # Excluding a bogus model should throw an error
        with self.assertRaisesMessage(
            management.CommandError, "Unknown model: fixtures.FooModel"
        ):
            self._dumpdata_assert(
                ["fixtures", "sites"], "", exclude_list=["fixtures.FooModel"]
            )