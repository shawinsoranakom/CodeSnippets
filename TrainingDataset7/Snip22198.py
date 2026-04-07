def test_circular_reference_natural_key(self):
        management.call_command(
            "loaddata",
            "circular_reference_natural_key.json",
            verbosity=0,
        )
        obj_a = CircularA.objects.get()
        obj_b = CircularB.objects.get()
        self.assertEqual(obj_a.obj, obj_b)
        self.assertEqual(obj_b.obj, obj_a)
        self._dumpdata_assert(
            ["fixtures"],
            '[{"model": "fixtures.circulara", '
            '"fields": {"key": "x", "obj": ["y"]}}, '
            '{"model": "fixtures.circularb", '
            '"fields": {"key": "y", "obj": ["x"]}}]',
            natural_primary_keys=True,
            natural_foreign_keys=True,
        )