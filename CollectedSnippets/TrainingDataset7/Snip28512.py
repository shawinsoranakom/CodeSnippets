def test_inlineformset_factory_nulls_default_pks(self):
        """
        #24377 - If we're adding a new object, a parent's auto-generated pk
        from the model field default should be ignored as it's regenerated on
        the save request.

        Tests the case where both the parent and child have a UUID primary key.
        """
        FormSet = inlineformset_factory(UUIDPKParent, UUIDPKChild, fields="__all__")
        formset = FormSet()
        self.assertIsNone(formset.forms[0].fields["parent"].initial)