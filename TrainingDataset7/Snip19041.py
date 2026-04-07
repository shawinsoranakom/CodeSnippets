def test_db_default_field_excluded(self):
        # created_at is excluded when no db_default override is provided.
        with self.assertNumQueries(1) as ctx:
            DbDefaultModel.objects.bulk_create(
                [DbDefaultModel(name="foo"), DbDefaultModel(name="bar")]
            )
        created_at_quoted_name = connection.ops.quote_name("created_at")
        self.assertEqual(
            ctx[0]["sql"].count(created_at_quoted_name),
            1 if connection.features.can_return_rows_from_bulk_insert else 0,
        )
        # created_at is included when a db_default override is provided.
        with self.assertNumQueries(1) as ctx:
            DbDefaultModel.objects.bulk_create(
                [
                    DbDefaultModel(name="foo", created_at=timezone.now()),
                    DbDefaultModel(name="bar"),
                ]
            )
        self.assertEqual(
            ctx[0]["sql"].count(created_at_quoted_name),
            2 if connection.features.can_return_rows_from_bulk_insert else 1,
        )