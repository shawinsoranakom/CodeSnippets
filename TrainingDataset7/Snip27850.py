def test_each_field_should_have_an_editable_attribute(self):
        self.assertTrue(all(f.editable.__class__ == bool for f in self.all_fields))