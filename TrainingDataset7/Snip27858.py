def test_cardinality_m2m(self):
        m2m_type_fields = [
            f for f in self.all_fields if f.is_relation and f.many_to_many
        ]
        # Test classes are what we expect
        self.assertEqual(MANY_TO_MANY_CLASSES, {f.__class__ for f in m2m_type_fields})

        # Ensure all m2m reverses are m2m
        for field in m2m_type_fields:
            reverse_field = field.remote_field
            self.assertTrue(reverse_field.is_relation)
            self.assertTrue(reverse_field.many_to_many)
            self.assertTrue(reverse_field.related_model)