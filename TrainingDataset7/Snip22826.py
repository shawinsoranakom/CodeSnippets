def test_forms_with_file_fields(self):
        # FileFields are a special case because they take their data from the
        # request.FILES, not request.POST.
        class FileForm(Form):
            file1 = FileField()

        f = FileForm(auto_id=False)
        self.assertHTMLEqual(
            f.as_table(),
            "<tr><th>File1:</th><td>"
            '<input type="file" name="file1" required></td></tr>',
        )

        f = FileForm(data={}, files={}, auto_id=False)
        self.assertHTMLEqual(
            f.as_table(),
            "<tr><th>File1:</th><td>"
            '<ul class="errorlist"><li>This field is required.</li></ul>'
            '<input type="file" name="file1" aria-invalid="true" required></td></tr>',
        )

        f = FileForm(
            data={}, files={"file1": SimpleUploadedFile("name", b"")}, auto_id=False
        )
        self.assertHTMLEqual(
            f.as_table(),
            "<tr><th>File1:</th><td>"
            '<ul class="errorlist"><li>The submitted file is empty.</li></ul>'
            '<input type="file" name="file1" aria-invalid="true" required></td></tr>',
        )

        f = FileForm(
            data={}, files={"file1": "something that is not a file"}, auto_id=False
        )
        self.assertHTMLEqual(
            f.as_table(),
            "<tr><th>File1:</th><td>"
            '<ul class="errorlist"><li>No file was submitted. Check the '
            "encoding type on the form.</li></ul>"
            '<input type="file" name="file1" aria-invalid="true" required></td></tr>',
        )

        f = FileForm(
            data={},
            files={"file1": SimpleUploadedFile("name", b"some content")},
            auto_id=False,
        )
        self.assertHTMLEqual(
            f.as_table(),
            "<tr><th>File1:</th><td>"
            '<input type="file" name="file1" required></td></tr>',
        )
        self.assertTrue(f.is_valid())

        file1 = SimpleUploadedFile(
            "我隻氣墊船裝滿晒鱔.txt",
            "मेरी मँडराने वाली नाव सर्पमीनों से भरी ह".encode(),
        )
        f = FileForm(data={}, files={"file1": file1}, auto_id=False)
        self.assertHTMLEqual(
            f.as_table(),
            "<tr><th>File1:</th><td>"
            '<input type="file" name="file1" required></td></tr>',
        )

        # A required file field with initial data should not contain the
        # required HTML attribute. The file input is left blank by the user to
        # keep the existing, initial value.
        f = FileForm(initial={"file1": "resume.txt"}, auto_id=False)
        self.assertHTMLEqual(
            f.as_table(),
            '<tr><th>File1:</th><td><input type="file" name="file1"></td></tr>',
        )