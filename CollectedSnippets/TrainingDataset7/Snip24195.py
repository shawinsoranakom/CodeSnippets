def test_envelope(self):
        countries = Country.objects.annotate(envelope=functions.Envelope("mpoly"))
        for country in countries:
            self.assertTrue(country.envelope.equals(country.mpoly.envelope))