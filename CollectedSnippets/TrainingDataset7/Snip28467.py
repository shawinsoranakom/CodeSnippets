def test_custom_callback_in_meta(self):
        def callback(db_field, **kwargs):
            return forms.CharField(widget=forms.Textarea)

        class NewForm(forms.ModelForm):
            class Meta:
                model = Person
                fields = ["id", "name"]
                formfield_callback = callback

        for field in NewForm.base_fields.values():
            self.assertEqual(type(field.widget), forms.Textarea)