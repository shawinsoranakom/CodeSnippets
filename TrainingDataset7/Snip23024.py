def test_can_delete_extra_formset_forms(self):
        ChoiceFormFormset = formset_factory(form=Choice, can_delete=True, extra=2)
        formset = ChoiceFormFormset()
        self.assertEqual(len(formset), 2)
        self.assertIn("DELETE", formset.forms[0].fields)
        self.assertIn("DELETE", formset.forms[1].fields)