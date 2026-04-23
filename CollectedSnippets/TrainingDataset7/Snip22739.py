def test_urlfield(self):
        e = {
            "required": "REQUIRED",
            "invalid": "INVALID",
            "max_length": '"%(value)s" has more than %(limit_value)d characters.',
        }
        f = URLField(error_messages=e, max_length=17)
        self.assertFormErrors(["REQUIRED"], f.clean, "")
        self.assertFormErrors(["INVALID"], f.clean, "abc.c")
        self.assertFormErrors(
            ['"https://djangoproject.com" has more than 17 characters.'],
            f.clean,
            "djangoproject.com",
        )