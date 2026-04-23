def test_forward_reference_fk(self):
        management.call_command("loaddata", "forward_reference_fk.json", verbosity=0)
        t1, t2 = NaturalKeyThing.objects.all()
        self.assertEqual(t1.other_thing, t2)
        self.assertEqual(t2.other_thing, t1)
        self._dumpdata_assert(
            ["fixtures"],
            '[{"model": "fixtures.naturalkeything", "pk": 1, '
            '"fields": {"key": "t1", "other_thing": 2, "other_things": []}}, '
            '{"model": "fixtures.naturalkeything", "pk": 2, '
            '"fields": {"key": "t2", "other_thing": 1, "other_things": []}}]',
        )