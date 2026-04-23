def test_format_discovery(self):
        # Load fixture 1 again, using format discovery
        management.call_command("loaddata", "fixture1", verbosity=0)
        self.assertSequenceEqual(
            Article.objects.values_list("headline", flat=True),
            ["Time to reform copyright", "Poker has no place on ESPN"],
        )

        # Try to load fixture 2 using format discovery; this will fail
        # because there are two fixture2's in the fixtures directory
        msg = "Multiple fixtures named 'fixture2'"
        with self.assertRaisesMessage(management.CommandError, msg):
            management.call_command("loaddata", "fixture2", verbosity=0)

        # object list is unaffected
        self.assertSequenceEqual(
            Article.objects.values_list("headline", flat=True),
            ["Time to reform copyright", "Poker has no place on ESPN"],
        )

        # Dump the current contents of the database as a JSON fixture
        self._dumpdata_assert(
            ["fixtures"],
            '[{"pk": 1, "model": "fixtures.category", "fields": '
            '{"description": "Latest news stories", "title": "News Stories"}}, '
            '{"pk": 2, "model": "fixtures.article", "fields": '
            '{"headline": "Poker has no place on ESPN", '
            '"pub_date": "2006-06-16T12:00:00"}}, '
            '{"pk": 3, "model": "fixtures.article", "fields": '
            '{"headline": "Time to reform copyright", '
            '"pub_date": "2006-06-16T13:00:00"}}]',
        )

        # Load fixture 4 (compressed), using format discovery
        management.call_command("loaddata", "fixture4", verbosity=0)
        self.assertSequenceEqual(
            Article.objects.values_list("headline", flat=True),
            [
                "Django pets kitten",
                "Time to reform copyright",
                "Poker has no place on ESPN",
            ],
        )