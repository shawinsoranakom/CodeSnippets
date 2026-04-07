def test_field_type_overrides(self):
        form = FieldOverridesByFormMetaForm()
        self.assertIs(Category._meta.get_field("url").__class__, models.CharField)
        self.assertIsInstance(form.fields["url"], forms.URLField)