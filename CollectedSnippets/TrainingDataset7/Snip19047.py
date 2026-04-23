def test_multiple_batches(self):
        with self.assertNumQueries(4):
            Country.objects.bulk_create(
                [
                    Country(name="France", iso_two_letter="FR"),
                    Country(name="Canada", iso_two_letter="CA"),
                ],
                batch_size=1,
            )