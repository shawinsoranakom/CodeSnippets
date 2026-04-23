def test_clear_and_file_contradiction(self):
        """
        If the user submits a new file upload AND checks the clear checkbox,
        they get a validation error, and the bound redisplay of the form still
        includes the current file and the clear checkbox.
        """

        class DocumentForm(forms.ModelForm):
            class Meta:
                model = Document
                fields = "__all__"

        form = DocumentForm(
            files={"myfile": SimpleUploadedFile("something.txt", b"content")}
        )
        self.assertTrue(form.is_valid())
        doc = form.save(commit=False)
        form = DocumentForm(
            instance=doc,
            files={"myfile": SimpleUploadedFile("something.txt", b"content")},
            data={"myfile-clear": "true"},
        )
        self.assertTrue(not form.is_valid())
        self.assertEqual(
            form.errors["myfile"],
            ["Please either submit a file or check the clear checkbox, not both."],
        )
        rendered = str(form)
        self.assertIn("something.txt", rendered)
        self.assertIn("myfile-clear", rendered)