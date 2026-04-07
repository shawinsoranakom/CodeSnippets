def test_override_field(self):
        class WriterForm(forms.ModelForm):
            book = forms.CharField(required=False)

            class Meta:
                model = Writer
                fields = "__all__"

        wf = WriterForm({"name": "Richard Lockridge"})
        self.assertTrue(wf.is_valid())