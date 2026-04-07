def test_set_pk_and_query_efficiency(self):
        with self.assertNumQueries(1):
            countries = Country.objects.bulk_create(self.data)
        self.assertEqual(len(countries), 4)
        self.assertEqual(Country.objects.get(pk=countries[0].pk), countries[0])
        self.assertEqual(Country.objects.get(pk=countries[1].pk), countries[1])
        self.assertEqual(Country.objects.get(pk=countries[2].pk), countries[2])
        self.assertEqual(Country.objects.get(pk=countries[3].pk), countries[3])