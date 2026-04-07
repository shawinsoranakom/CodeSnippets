def test_dumpdata_with_pks(self):
        management.call_command("loaddata", "fixture1.json", verbosity=0)
        management.call_command("loaddata", "fixture2.json", verbosity=0)
        self._dumpdata_assert(
            ["fixtures.Article"],
            '[{"pk": 2, "model": "fixtures.article", '
            '"fields": {"headline": "Poker has no place on ESPN", '
            '"pub_date": "2006-06-16T12:00:00"}}, '
            '{"pk": 3, "model": "fixtures.article", "fields": '
            '{"headline": "Copyright is fine the way it is", '
            '"pub_date": "2006-06-16T14:00:00"}}]',
            primary_keys="2,3",
        )

        self._dumpdata_assert(
            ["fixtures.Article"],
            '[{"pk": 2, "model": "fixtures.article", '
            '"fields": {"headline": "Poker has no place on ESPN", '
            '"pub_date": "2006-06-16T12:00:00"}}]',
            primary_keys="2",
        )

        with self.assertRaisesMessage(
            management.CommandError, "You can only use --pks option with one model"
        ):
            self._dumpdata_assert(
                ["fixtures"],
                '[{"pk": 2, "model": "fixtures.article", "fields": '
                '{"headline": "Poker has no place on ESPN", '
                '"pub_date": "2006-06-16T12:00:00"}}, '
                '{"pk": 3, "model": "fixtures.article", "fields": '
                '{"headline": "Copyright is fine the way it is", '
                '"pub_date": "2006-06-16T14:00:00"}}]',
                primary_keys="2,3",
            )

        with self.assertRaisesMessage(
            management.CommandError, "You can only use --pks option with one model"
        ):
            self._dumpdata_assert(
                "",
                '[{"pk": 2, "model": "fixtures.article", "fields": '
                '{"headline": "Poker has no place on ESPN", '
                '"pub_date": "2006-06-16T12:00:00"}}, '
                '{"pk": 3, "model": "fixtures.article", "fields": '
                '{"headline": "Copyright is fine the way it is", '
                '"pub_date": "2006-06-16T14:00:00"}}]',
                primary_keys="2,3",
            )

        with self.assertRaisesMessage(
            management.CommandError, "You can only use --pks option with one model"
        ):
            self._dumpdata_assert(
                ["fixtures.Article", "fixtures.category"],
                '[{"pk": 2, "model": "fixtures.article", "fields": '
                '{"headline": "Poker has no place on ESPN", '
                '"pub_date": "2006-06-16T12:00:00"}}, '
                '{"pk": 3, "model": "fixtures.article", "fields": '
                '{"headline": "Copyright is fine the way it is", '
                '"pub_date": "2006-06-16T14:00:00"}}]',
                primary_keys="2,3",
            )