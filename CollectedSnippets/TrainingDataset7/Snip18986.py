def test_efficiency(self):
        with self.assertNumQueries(1):
            Country.objects.bulk_create(self.data)