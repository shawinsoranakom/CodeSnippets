def _test_update_conflicts_unique_two_fields(self, unique_fields):
        Country.objects.bulk_create(self.data)
        self.assertEqual(Country.objects.count(), 4)

        new_data = [
            # Conflicting countries.
            Country(
                name="Germany",
                iso_two_letter="DE",
                description=("Germany is a country in Central Europe."),
            ),
            Country(
                name="Czech Republic",
                iso_two_letter="CZ",
                description=(
                    "The Czech Republic is a landlocked country in Central Europe."
                ),
            ),
            # New countries.
            Country(name="Australia", iso_two_letter="AU"),
            Country(
                name="Japan",
                iso_two_letter="JP",
                description=("Japan is an island country in East Asia."),
            ),
        ]
        results = Country.objects.bulk_create(
            new_data,
            update_conflicts=True,
            update_fields=["description"],
            unique_fields=unique_fields,
        )
        self.assertEqual(len(results), len(new_data))
        if connection.features.can_return_rows_from_bulk_insert:
            for instance in results:
                self.assertIsNotNone(instance.pk)
        self.assertEqual(Country.objects.count(), 6)
        self.assertCountEqual(
            Country.objects.values("iso_two_letter", "description"),
            [
                {"iso_two_letter": "US", "description": ""},
                {"iso_two_letter": "NL", "description": ""},
                {
                    "iso_two_letter": "DE",
                    "description": ("Germany is a country in Central Europe."),
                },
                {
                    "iso_two_letter": "CZ",
                    "description": (
                        "The Czech Republic is a landlocked country in Central Europe."
                    ),
                },
                {"iso_two_letter": "AU", "description": ""},
                {
                    "iso_two_letter": "JP",
                    "description": ("Japan is an island country in East Asia."),
                },
            ],
        )