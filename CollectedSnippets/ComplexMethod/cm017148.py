def test_cardinality_m2o(self):
        m2o_type_fields = [
            f
            for f in self.fields_and_reverse_objects
            if f.is_relation and f.many_to_one
        ]
        # Test classes are what we expect
        self.assertEqual(MANY_TO_ONE_CLASSES, {f.__class__ for f in m2o_type_fields})

        # Ensure all m2o reverses are o2m
        for obj in m2o_type_fields:
            if hasattr(obj, "field"):
                reverse_field = obj.field
                self.assertTrue(reverse_field.is_relation and reverse_field.one_to_many)