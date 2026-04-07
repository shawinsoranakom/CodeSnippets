def test_modelformset_factory_disable_delete_extra(self):
        AuthorFormSet = modelformset_factory(
            Author,
            fields="__all__",
            can_delete=True,
            can_delete_extra=False,
            extra=2,
        )
        formset = AuthorFormSet()
        self.assertEqual(len(formset), 2)
        self.assertNotIn("DELETE", formset.forms[0].fields)
        self.assertNotIn("DELETE", formset.forms[1].fields)