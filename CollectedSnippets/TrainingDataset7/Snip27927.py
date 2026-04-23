def test_save_field_with_db_converters(self):
        obj = GeneratedModelFieldWithConverters.objects.create(field=uuid.uuid4())
        obj.field = uuid.uuid4()
        expected_num_queries = (
            0 if connection.features.can_return_rows_from_update else 1
        )
        obj.save(update_fields={"field"})
        with self.assertNumQueries(expected_num_queries):
            self.assertEqual(obj.field, obj.field_copy)