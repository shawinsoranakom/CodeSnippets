def test_all_field_types_should_have_flags(self):
        for field in self.fields_and_reverse_objects:
            for flag in FLAG_PROPERTIES:
                self.assertTrue(
                    hasattr(field, flag),
                    "Field %s does not have flag %s" % (field, flag),
                )
            if field.is_relation:
                true_cardinality_flags = sum(
                    getattr(field, flag) is True
                    for flag in FLAG_PROPERTIES_FOR_RELATIONS
                )
                # If the field has a relation, there should be only one of the
                # 4 cardinality flags available.
                self.assertEqual(1, true_cardinality_flags)