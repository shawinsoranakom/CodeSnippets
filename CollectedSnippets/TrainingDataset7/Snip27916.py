def test_save_model_with_foreign_key(self):
        fk_object = Foo.objects.create(a="abc", d=Decimal("12.34"))
        m = self.base_model(a=1, b=2, fk=fk_object)
        m.save()
        expected_num_queries = (
            0 if connection.features.can_return_columns_from_insert else 1
        )
        with self.assertNumQueries(expected_num_queries):
            self.assertEqual(m.field, 3)