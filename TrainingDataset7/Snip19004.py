def test_max_batch_size(self):
        objs = [Country(name=f"Country {i}") for i in range(1000)]
        fields = ["name", "iso_two_letter", "description"]
        max_batch_size = connection.ops.bulk_batch_size(fields, objs)
        with self.assertNumQueries(ceil(len(objs) / max_batch_size)):
            Country.objects.bulk_create(objs)