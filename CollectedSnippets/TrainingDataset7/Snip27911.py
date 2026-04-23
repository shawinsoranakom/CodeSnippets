def test_full_clean_with_unique_constraint_expression(self):
        model_name = self.unique_constraint_model._meta.verbose_name.capitalize()

        m = self.unique_constraint_model(a=2)
        m.full_clean()
        m.save()
        expected_num_queries = (
            0 if connection.features.can_return_columns_from_insert else 1
        )
        with self.assertNumQueries(expected_num_queries):
            self.assertEqual(m.a_squared, 4)

        m = self.unique_constraint_model(a=2)
        with self.assertRaises(ValidationError) as cm:
            m.full_clean()
        self.assertEqual(
            cm.exception.message_dict,
            {"__all__": [f"Constraint “{model_name} a” is violated."]},
        )