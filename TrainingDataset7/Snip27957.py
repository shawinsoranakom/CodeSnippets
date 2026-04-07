def test_documented_range(self):
        """
        Values within the documented safe range pass validation, and can be
        saved and retrieved without corruption.
        """
        min_value, max_value = self.documented_range

        instance = self.model(value=min_value)
        instance.full_clean()
        instance.save()
        qs = self.model.objects.filter(value__lte=min_value)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs[0].value, min_value)

        instance = self.model(value=max_value)
        instance.full_clean()
        instance.save()
        qs = self.model.objects.filter(value__gte=max_value)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs[0].value, max_value)