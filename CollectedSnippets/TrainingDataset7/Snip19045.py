def test_no_unnecessary_transaction(self):
        unused_id = self.get_unused_country_id()
        with self.assertNumQueries(1):
            Country.objects.bulk_create(
                [Country(id=unused_id, name="France", iso_two_letter="FR")]
            )
        with self.assertNumQueries(1):
            Country.objects.bulk_create([Country(name="Canada", iso_two_letter="CA")])