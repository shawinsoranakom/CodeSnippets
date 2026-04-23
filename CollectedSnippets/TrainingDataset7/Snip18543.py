def test_bulk_batch_size_unlimited(self):
        objects = range(2**16 + 1)
        first_name_field = Person._meta.get_field("first_name")
        last_name_field = Person._meta.get_field("last_name")
        composite_pk = models.CompositePrimaryKey("first_name", "last_name")
        composite_pk.fields = [first_name_field, last_name_field]

        self.assertEqual(connection.ops.bulk_batch_size([], objects), len(objects))
        self.assertEqual(
            connection.ops.bulk_batch_size([first_name_field], objects),
            len(objects),
        )
        self.assertEqual(
            connection.ops.bulk_batch_size(
                [first_name_field, last_name_field], objects
            ),
            len(objects),
        )
        self.assertEqual(
            connection.ops.bulk_batch_size([composite_pk, first_name_field], objects),
            len(objects),
        )