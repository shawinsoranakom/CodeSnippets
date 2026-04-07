def test_custom_get_form_with_fieldsets(self):
        """
        The fieldsets checks are skipped when the ModelAdmin.get_form() method
        is overridden.
        """
        errors = ValidFormFieldsets(Song, AdminSite()).check()
        self.assertEqual(errors, [])