def test_forward_reference_m2m(self):
        management.call_command("loaddata", "forward_reference_m2m.json", verbosity=0)
        self.assertEqual(NaturalKeyThing.objects.count(), 3)
        t1 = NaturalKeyThing.objects.get_by_natural_key("t1")
        self.assertSequenceEqual(
            t1.other_things.order_by("key").values_list("key", flat=True),
            ["t2", "t3"],
        )
        self._dumpdata_assert(
            ["fixtures"],
            '[{"model": "fixtures.naturalkeything", "pk": 1, '
            '"fields": {"key": "t1", "other_thing": null, "other_things": [2, 3]}}, '
            '{"model": "fixtures.naturalkeything", "pk": 2, '
            '"fields": {"key": "t2", "other_thing": null, "other_things": []}}, '
            '{"model": "fixtures.naturalkeything", "pk": 3, '
            '"fields": {"key": "t3", "other_thing": null, "other_things": []}}]',
        )