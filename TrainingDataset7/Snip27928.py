def test_create_with_non_auto_pk(self):
        obj = GeneratedModelNonAutoPk.objects.create(id=1, a=2)
        self.assertEqual(obj.id, 1)
        self.assertEqual(obj.a, 2)
        self.assertEqual(obj.b, 3)