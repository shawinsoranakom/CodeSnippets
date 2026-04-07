def test_update_all(self):
        """
        In the rare case you want to update every instance of a model, update()
        is also a manager method.
        """
        self.assertEqual(DataPoint.objects.update(value="thing"), 3)
        resp = DataPoint.objects.values("value").distinct()
        self.assertEqual(list(resp), [{"value": "thing"}])