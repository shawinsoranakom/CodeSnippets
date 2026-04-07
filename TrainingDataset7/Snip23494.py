def test_disable_delete_extra(self):
        GenericFormSet = generic_inlineformset_factory(
            TaggedItem,
            can_delete=True,
            can_delete_extra=False,
            extra=2,
        )
        formset = GenericFormSet()
        self.assertEqual(len(formset), 2)
        self.assertNotIn("DELETE", formset.forms[0].fields)
        self.assertNotIn("DELETE", formset.forms[1].fields)