def test_long_and_short_text(self):
        Country.objects.bulk_create(
            [
                Country(description="a" * 4001, iso_two_letter="A"),
                Country(description="a", iso_two_letter="B"),
                Country(description="Ж" * 2001, iso_two_letter="C"),
                Country(description="Ж", iso_two_letter="D"),
            ]
        )
        self.assertEqual(Country.objects.count(), 4)