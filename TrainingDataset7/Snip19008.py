def test_set_pk_and_insert_single_item(self):
        with self.assertNumQueries(1):
            countries = Country.objects.bulk_create([self.data[0]])
        self.assertEqual(len(countries), 1)
        self.assertEqual(Country.objects.get(pk=countries[0].pk), countries[0])