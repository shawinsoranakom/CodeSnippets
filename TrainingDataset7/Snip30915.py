def test_datetime_callable_default_all(self):
        self.assert_pickles(Happening.objects.all())