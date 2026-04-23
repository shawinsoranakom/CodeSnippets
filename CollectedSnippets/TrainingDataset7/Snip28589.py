def test_inlineformset_factory_can_not_delete_extra(self):
        BookFormSet = inlineformset_factory(
            Author,
            Book,
            fields="__all__",
            can_delete=True,
            can_delete_extra=False,
            extra=2,
        )
        formset = BookFormSet()
        self.assertEqual(len(formset), 2)
        self.assertNotIn("DELETE", formset.forms[0].fields)
        self.assertNotIn("DELETE", formset.forms[1].fields)