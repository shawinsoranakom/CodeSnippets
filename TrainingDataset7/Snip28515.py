def test_inlineformset_factory_nulls_default_pks_auto_parent_uuid_child(self):
        """
        #24958 - Variant of test_inlineformset_factory_nulls_default_pks for
        the case of a parent object with an AutoField primary key and a child
        object with a UUID primary key.
        """
        FormSet = inlineformset_factory(
            AutoPKParent, UUIDPKChildOfAutoPKParent, fields="__all__"
        )
        formset = FormSet()
        self.assertIsNone(formset.forms[0].fields["parent"].initial)