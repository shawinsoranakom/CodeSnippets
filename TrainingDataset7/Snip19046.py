def test_objs_with_and_without_pk(self):
        unused_id = self.get_unused_country_id()
        with self.assertNumQueries(4):
            Country.objects.bulk_create(
                [
                    Country(id=unused_id, name="France", iso_two_letter="FR"),
                    Country(name="Canada", iso_two_letter="CA"),
                ]
            )