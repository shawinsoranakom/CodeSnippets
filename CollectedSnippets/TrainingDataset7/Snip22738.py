def test_filefield(self):
        e = {
            "required": "REQUIRED",
            "invalid": "INVALID",
            "missing": "MISSING",
            "empty": "EMPTY FILE",
        }
        f = FileField(error_messages=e)
        self.assertFormErrors(["REQUIRED"], f.clean, "")
        self.assertFormErrors(["INVALID"], f.clean, "abc")
        self.assertFormErrors(["EMPTY FILE"], f.clean, SimpleUploadedFile("name", None))
        self.assertFormErrors(["EMPTY FILE"], f.clean, SimpleUploadedFile("name", ""))