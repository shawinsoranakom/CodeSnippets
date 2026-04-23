def test_field_name(self):
        """
        A defined field name (name="fieldname") is used instead of the model
        model's attribute name (modelname).
        """
        instance = RenamedField()
        self.assertTrue(hasattr(instance, "get_fieldname_display"))
        self.assertFalse(hasattr(instance, "get_modelname_display"))