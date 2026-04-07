def test_fixtures_loaded(self):
        count = Absolute.objects.count()
        self.assertGreater(count, 0, "Fixtures not loaded properly.")