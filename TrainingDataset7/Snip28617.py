def test_modelformset_factory_default(self):
        Formset = modelformset_factory(UserSite, form=UserSiteForm)
        form = Formset().forms[0]
        self.assertIsInstance(form["id"].field.widget, CustomWidget)
        self.assertIsInstance(form["data"].field.widget, CustomWidget)
        self.assertFalse(form.fields["id"].localize)
        self.assertTrue(form.fields["data"].localize)