def test_circular_reference(self):
        management.call_command("loaddata", "circular_reference.json", verbosity=0)
        obj_a = CircularA.objects.get()
        obj_b = CircularB.objects.get()
        self.assertEqual(obj_a.obj, obj_b)
        self.assertEqual(obj_b.obj, obj_a)
        self._dumpdata_assert(
            ["fixtures"],
            '[{"model": "fixtures.circulara", "pk": 1, '
            '"fields": {"key": "x", "obj": 1}}, '
            '{"model": "fixtures.circularb", "pk": 1, '
            '"fields": {"key": "y", "obj": 1}}]',
        )