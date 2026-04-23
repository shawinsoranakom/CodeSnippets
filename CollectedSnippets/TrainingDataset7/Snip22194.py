def test_forward_reference_fk_natural_key(self):
        management.call_command(
            "loaddata",
            "forward_reference_fk_natural_key.json",
            verbosity=0,
        )
        t1, t2 = NaturalKeyThing.objects.all()
        self.assertEqual(t1.other_thing, t2)
        self.assertEqual(t2.other_thing, t1)
        self._dumpdata_assert(
            ["fixtures"],
            '[{"model": "fixtures.naturalkeything", '
            '"fields": {"key": "t1", "other_thing": ["t2"], "other_things": []}}, '
            '{"model": "fixtures.naturalkeything", '
            '"fields": {"key": "t2", "other_thing": ["t1"], "other_things": []}}]',
            natural_primary_keys=True,
            natural_foreign_keys=True,
        )