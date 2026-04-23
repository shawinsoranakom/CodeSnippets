def test_filefield_with_fileinput_required(self):
        class FileForm(Form):
            file1 = FileField(widget=FileInput)

        f = FileForm(auto_id=False)
        self.assertHTMLEqual(
            f.as_table(),
            "<tr><th>File1:</th><td>"
            '<input type="file" name="file1" required></td></tr>',
        )
        # A required file field with initial data doesn't contain the required
        # HTML attribute. The file input is left blank by the user to keep the
        # existing, initial value.
        f = FileForm(initial={"file1": "resume.txt"}, auto_id=False)
        self.assertHTMLEqual(
            f.as_table(),
            '<tr><th>File1:</th><td><input type="file" name="file1"></td></tr>',
        )