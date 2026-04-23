def test_filefield_initial_callable(self):
        class FileForm(Form):
            file1 = FileField(initial=lambda: "resume.txt")

        f = FileForm({})
        self.assertEqual(f.errors, {})
        self.assertEqual(f.cleaned_data["file1"], "resume.txt")