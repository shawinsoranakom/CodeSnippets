def test_cardinality_o2m(self):
        o2m_type_fields = [
            f
            for f in self.fields_and_reverse_objects
            if f.is_relation and f.one_to_many
        ]
        # Test classes are what we expect
        self.assertEqual(ONE_TO_MANY_CLASSES, {f.__class__ for f in o2m_type_fields})

        # Ensure all o2m reverses are m2o
        for field in o2m_type_fields:
            if field.concrete:
                reverse_field = field.remote_field
                self.assertTrue(reverse_field.is_relation and reverse_field.many_to_one)