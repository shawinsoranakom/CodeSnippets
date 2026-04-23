def test_backend_range_min_value_lookups(self):
        min_value = self.backend_range[0]
        if min_value is None:
            raise SkipTest("Backend doesn't define an integer min value.")
        underflow_value = min_value - 1
        self.model.objects.create(value=min_value)
        # A refresh of obj is necessary because last_insert_id() is bugged
        # on MySQL and returns invalid values.
        obj = self.model.objects.get(value=min_value)
        with self.assertNumQueries(0), self.assertRaises(self.model.DoesNotExist):
            self.model.objects.get(value=underflow_value)
        with self.assertNumQueries(1):
            self.assertEqual(self.model.objects.get(value__gt=underflow_value), obj)
        with self.assertNumQueries(1):
            self.assertEqual(self.model.objects.get(value__gte=underflow_value), obj)
        with self.assertNumQueries(0), self.assertRaises(self.model.DoesNotExist):
            self.model.objects.get(value__lt=underflow_value)
        with self.assertNumQueries(0), self.assertRaises(self.model.DoesNotExist):
            self.model.objects.get(value__lte=underflow_value)