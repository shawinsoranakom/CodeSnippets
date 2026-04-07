def test_inlineformset_factory_default(self):
        Formset = inlineformset_factory(
            User, UserSite, form=UserSiteForm, fields="__all__"
        )
        form = Formset().forms[0]
        self.assertIsInstance(form["id"].field.widget, CustomWidget)
        self.assertIsInstance(form["data"].field.widget, CustomWidget)
        self.assertFalse(form.fields["id"].localize)
        self.assertTrue(form.fields["data"].localize)