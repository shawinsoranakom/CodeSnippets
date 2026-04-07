def test_o2o_primary_key_delete(self):
        t = Target.objects.create(name="name")
        Pointer.objects.create(other=t)
        num_deleted, objs = Pointer.objects.filter(other__name="name").delete()
        self.assertEqual(num_deleted, 1)
        self.assertEqual(objs, {"one_to_one.Pointer": 1})