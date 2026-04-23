def test_multiple_error(self):
        msg = "FileInput doesn't support uploading multiple files."
        with self.assertRaisesMessage(ValueError, msg):
            FileInput(attrs={"multiple": True})