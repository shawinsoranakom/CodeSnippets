def test_dumpdata_objects_with_prefetch_related(self):
        management.call_command(
            "loaddata", "fixture6.json", "fixture8.json", verbosity=0
        )
        with self.assertNumQueries(5):
            self._dumpdata_assert(
                ["fixtures.visa"],
                '[{"fields": {"permissions": [["add_user", "auth", "user"]],'
                '"person": ["Stephane Grappelli"]},'
                '"model": "fixtures.visa", "pk": 2},'
                '{"fields": {"permissions": [], "person": ["Prince"]},'
                '"model": "fixtures.visa", "pk": 3}]',
                natural_foreign_keys=True,
                primary_keys="2,3",
            )