def test_inlineformset_factory_ignores_default_pks_on_submit(self):
        """
        #24377 - Inlines with a model field default should ignore that default
        value to avoid triggering validation on empty forms.
        """
        FormSet = inlineformset_factory(UUIDPKParent, UUIDPKChild, fields="__all__")
        formset = FormSet(
            {
                "uuidpkchild_set-TOTAL_FORMS": 3,
                "uuidpkchild_set-INITIAL_FORMS": 0,
                "uuidpkchild_set-MAX_NUM_FORMS": "",
                "uuidpkchild_set-0-name": "Foo",
                "uuidpkchild_set-1-name": "",
                "uuidpkchild_set-2-name": "",
            }
        )
        self.assertTrue(formset.is_valid())
        self.assertIsNone(formset.instance.uuid)
        self.assertIsNone(formset.forms[0].instance.parent_id)