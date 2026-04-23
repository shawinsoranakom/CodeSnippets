def test_update(self):
        m = self.base_model.objects.create(a=1, b=2)
        self.base_model.objects.update(b=3)
        m = self.base_model.objects.get(pk=m.pk)
        self.assertEqual(m.field, 4)