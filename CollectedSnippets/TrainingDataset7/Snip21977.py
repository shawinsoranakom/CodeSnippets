def test_filename_case_preservation(self):
        """
        The storage backend shouldn't mess with the case of the filenames
        uploaded.
        """
        # Synthesize the contents of a file upload with a mixed case filename
        # so we don't have to carry such a file in the Django tests source code
        # tree.
        vars = {"boundary": "oUrBoUnDaRyStRiNg"}
        post_data = [
            "--%(boundary)s",
            'Content-Disposition: form-data; name="file_field"; '
            'filename="MiXeD_cAsE.txt"',
            "Content-Type: application/octet-stream",
            "",
            "file contents\n",
            "--%(boundary)s--\r\n",
        ]
        response = self.client.post(
            "/filename_case/",
            "\r\n".join(post_data) % vars,
            "multipart/form-data; boundary=%(boundary)s" % vars,
        )
        self.assertEqual(response.status_code, 200)
        id = int(response.content)
        obj = FileModel.objects.get(pk=id)
        # The name of the file uploaded and the file stored in the server-side
        # shouldn't differ.
        self.assertEqual(os.path.basename(obj.testfile.path), "MiXeD_cAsE.txt")