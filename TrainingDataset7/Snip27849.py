def test_each_field_should_have_a_concrete_attribute(self):
        self.assertTrue(all(f.concrete.__class__ == bool for f in self.fields))