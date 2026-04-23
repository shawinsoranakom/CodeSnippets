def test_inlineformset_factory_can_delete_extra(self):
        BookFormSet = inlineformset_factory(
            Author,
            Book,
            fields="__all__",
            can_delete=True,
            can_delete_extra=True,
            extra=2,
        )
        formset = BookFormSet()
        self.assertEqual(len(formset), 2)
        self.assertIn("DELETE", formset.forms[0].fields)
        self.assertIn("DELETE", formset.forms[1].fields)