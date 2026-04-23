def test_bulk_batch_size_limited(self):
        max_query_params = connection.features.max_query_params
        objects = range(max_query_params + 1)
        first_name_field = Person._meta.get_field("first_name")
        last_name_field = Person._meta.get_field("last_name")
        composite_pk = models.CompositePrimaryKey("first_name", "last_name")
        composite_pk.fields = [first_name_field, last_name_field]

        self.assertEqual(connection.ops.bulk_batch_size([], objects), len(objects))
        self.assertEqual(
            connection.ops.bulk_batch_size([first_name_field], objects),
            max_query_params,
        )
        self.assertEqual(
            connection.ops.bulk_batch_size(
                [first_name_field, last_name_field], objects
            ),
            max_query_params // 2,
        )
        self.assertEqual(
            connection.ops.bulk_batch_size([composite_pk, first_name_field], objects),
            max_query_params // 3,
        )