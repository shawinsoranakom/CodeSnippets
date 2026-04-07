def test_modelformset_factory_without_fields(self):
        """Regression for #19733"""
        message = (
            "Calling modelformset_factory without defining 'fields' or 'exclude' "
            "explicitly is prohibited."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            modelformset_factory(Author)