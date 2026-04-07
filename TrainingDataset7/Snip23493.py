def test_can_delete_extra(self):
        GenericFormSet = generic_inlineformset_factory(
            TaggedItem,
            can_delete=True,
            can_delete_extra=True,
            extra=2,
        )
        formset = GenericFormSet()
        self.assertEqual(len(formset), 2)
        self.assertIn("DELETE", formset.forms[0].fields)
        self.assertIn("DELETE", formset.forms[1].fields)