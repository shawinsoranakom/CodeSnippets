def test_update(self):
        """
        Objects are updated by first filtering the candidates into a queryset
        and then calling the update() method. It executes immediately and
        returns nothing.
        """
        resp = DataPoint.objects.filter(value="apple").update(name="d1")
        self.assertEqual(resp, 1)
        resp = DataPoint.objects.filter(value="apple")
        self.assertEqual(list(resp), [self.d0])