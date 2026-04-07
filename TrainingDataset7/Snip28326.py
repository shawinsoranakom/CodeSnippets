def test_save_blank_false_with_required_false(self):
        """
        A ModelForm with a model with a field set to blank=False and the form
        field set to required=False should allow the field to be unset.
        """
        obj = Writer.objects.create(name="test")
        form = CustomWriterForm(data={"name": ""}, instance=obj)
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertEqual(obj.name, "")