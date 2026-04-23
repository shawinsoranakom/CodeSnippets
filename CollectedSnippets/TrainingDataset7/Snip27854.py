def test_non_editable_fields(self):
        for field in self.all_fields:
            if type(field) in NON_EDITABLE_FIELDS:
                self.assertFalse(field.editable)
            else:
                self.assertTrue(field.editable)