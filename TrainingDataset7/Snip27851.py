def test_each_field_should_have_a_has_rel_attribute(self):
        self.assertTrue(all(f.is_relation.__class__ == bool for f in self.all_fields))