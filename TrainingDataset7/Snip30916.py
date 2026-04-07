def test_datetime_callable_default_filter(self):
        self.assert_pickles(Happening.objects.filter(when=datetime.datetime.now()))