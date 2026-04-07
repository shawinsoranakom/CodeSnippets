def test_form_kwargs_empty_form(self):
        FormSet = formset_factory(CustomKwargForm)
        formset = FormSet(form_kwargs={"custom_kwarg": 1})
        self.assertTrue(hasattr(formset.empty_form, "custom_kwarg"))
        self.assertEqual(formset.empty_form.custom_kwarg, 1)