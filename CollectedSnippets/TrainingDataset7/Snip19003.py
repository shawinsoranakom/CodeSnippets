def test_explicit_batch_size_respects_max_batch_size(self):
        objs = [Country(name=f"Country {i}") for i in range(1000)]
        fields = ["name", "iso_two_letter", "description"]
        max_batch_size = max(connection.ops.bulk_batch_size(fields, objs), 1)
        with self.assertNumQueries(ceil(len(objs) / max_batch_size)):
            Country.objects.bulk_create(objs, batch_size=max_batch_size + 1)