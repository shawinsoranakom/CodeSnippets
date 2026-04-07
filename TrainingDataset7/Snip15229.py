def test_custom_modelforms_with_fields_fieldsets(self):
        """
        # Regression test for #8027: custom ModelForms with fields/fieldsets
        """
        errors = ValidFields(Song, AdminSite()).check()
        self.assertEqual(errors, [])