def test_modelformset_factory_can_delete_extra(self):
        AuthorFormSet = modelformset_factory(
            Author,
            fields="__all__",
            can_delete=True,
            can_delete_extra=True,
            extra=2,
        )
        formset = AuthorFormSet()
        self.assertEqual(len(formset), 2)
        self.assertIn("DELETE", formset.forms[0].fields)
        self.assertIn("DELETE", formset.forms[1].fields)