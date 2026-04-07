def test_inlineformset_factory_nulls_default_pks_alternate_key_relation(self):
        """
        #24958 - Variant of test_inlineformset_factory_nulls_default_pks for
        the case of a parent object with a UUID alternate key and a child
        object that relates to that alternate key.
        """
        FormSet = inlineformset_factory(
            ParentWithUUIDAlternateKey, ChildRelatedViaAK, fields="__all__"
        )
        formset = FormSet()
        self.assertIsNone(formset.forms[0].fields["parent"].initial)