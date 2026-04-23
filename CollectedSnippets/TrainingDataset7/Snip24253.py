def test_fixtures(self):
        "Testing geographic model initialization from fixtures."
        # Ensuring that data was loaded from initial data fixtures.
        self.assertEqual(2, Country.objects.count())
        self.assertEqual(8, City.objects.count())
        self.assertEqual(2, State.objects.count())