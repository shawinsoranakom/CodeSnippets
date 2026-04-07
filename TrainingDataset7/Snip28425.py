def test_full_clear(self):
        """
        Integration happy-path test that a model FileField can actually be set
        and cleared via a ModelForm.
        """

        class DocumentForm(forms.ModelForm):
            class Meta:
                model = Document
                fields = "__all__"

        form = DocumentForm()
        self.assertIn('name="myfile"', str(form))
        self.assertNotIn("myfile-clear", str(form))
        form = DocumentForm(
            files={"myfile": SimpleUploadedFile("something.txt", b"content")}
        )
        self.assertTrue(form.is_valid())
        doc = form.save(commit=False)
        self.assertEqual(doc.myfile.name, "something.txt")
        form = DocumentForm(instance=doc)
        self.assertIn("myfile-clear", str(form))
        form = DocumentForm(instance=doc, data={"myfile-clear": "true"})
        doc = form.save(commit=False)
        self.assertFalse(doc.myfile)