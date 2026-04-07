def test_backend_range_max_value_lookups(self):
        max_value = self.backend_range[-1]
        if max_value is None:
            raise SkipTest("Backend doesn't define an integer max value.")
        overflow_value = max_value + 1
        obj = self.model.objects.create(value=max_value)
        with self.assertNumQueries(0), self.assertRaises(self.model.DoesNotExist):
            self.model.objects.get(value=overflow_value)
        with self.assertNumQueries(0), self.assertRaises(self.model.DoesNotExist):
            self.model.objects.get(value__gt=overflow_value)
        with self.assertNumQueries(0), self.assertRaises(self.model.DoesNotExist):
            self.model.objects.get(value__gte=overflow_value)
        with self.assertNumQueries(1):
            self.assertEqual(self.model.objects.get(value__lt=overflow_value), obj)
        with self.assertNumQueries(1):
            self.assertEqual(self.model.objects.get(value__lte=overflow_value), obj)