def test_bulk_update(self):
        m = self.base_model.objects.create(a=1, b=2)
        m.a = 3
        self.base_model.objects.bulk_update([m], fields=["a"])
        m = self.base_model.objects.get(pk=m.pk)
        self.assertEqual(m.field, 5)