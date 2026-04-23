def test_cardinality_o2o(self):
        o2o_type_fields = [f for f in self.all_fields if f.is_relation and f.one_to_one]
        # Test classes are what we expect
        self.assertEqual(ONE_TO_ONE_CLASSES, {f.__class__ for f in o2o_type_fields})

        # Ensure all o2o reverses are o2o
        for obj in o2o_type_fields:
            if hasattr(obj, "field"):
                reverse_field = obj.field
                self.assertTrue(reverse_field.is_relation and reverse_field.one_to_one)