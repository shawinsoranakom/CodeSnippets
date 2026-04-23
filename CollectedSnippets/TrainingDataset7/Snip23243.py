def test_multiple_error(self):
        msg = "ClearableFileInput doesn't support uploading multiple files."
        with self.assertRaisesMessage(ValueError, msg):
            ClearableFileInput(attrs={"multiple": True})