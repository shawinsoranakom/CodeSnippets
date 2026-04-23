def test_modelform_factory_with_all_fields(self):
        """Regression for #19733"""
        form = modelform_factory(Person, fields="__all__")
        self.assertEqual(list(form.base_fields), ["name"])