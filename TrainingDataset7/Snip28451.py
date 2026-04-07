def test_field_removal_name_clashes(self):
        """
        Form fields can be removed in subclasses by setting them to None
        (#22510).
        """

        class MyForm(forms.ModelForm):
            media = forms.CharField()

            class Meta:
                model = Writer
                fields = "__all__"

        class SubForm(MyForm):
            media = None

        self.assertIn("media", MyForm().fields)
        self.assertNotIn("media", SubForm().fields)
        self.assertTrue(hasattr(MyForm, "media"))
        self.assertTrue(hasattr(SubForm, "media"))