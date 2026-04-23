def test_create_field_with_db_converters(self):
        obj = GeneratedModelFieldWithConverters.objects.create(field=uuid.uuid4())
        expected_num_queries = (
            0 if connection.features.can_return_columns_from_insert else 1
        )
        with self.assertNumQueries(expected_num_queries):
            self.assertEqual(obj.field, obj.field_copy)