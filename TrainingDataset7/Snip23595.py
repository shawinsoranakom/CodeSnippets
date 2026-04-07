def test_editable_generic_rel(self):
        GenericRelationForm = modelform_factory(HasLinkThing, fields="__all__")
        form = GenericRelationForm()
        self.assertIn("links", form.fields)
        form = GenericRelationForm({"links": None})
        self.assertTrue(form.is_valid())
        form.save()
        links = HasLinkThing._meta.get_field("links")
        self.assertEqual(links.save_form_data_calls, 1)