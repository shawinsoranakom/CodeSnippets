def test_emailfield(self):
        e = {
            "required": "REQUIRED",
            "invalid": "INVALID",
            "min_length": "LENGTH %(show_value)s, MIN LENGTH %(limit_value)s",
            "max_length": "LENGTH %(show_value)s, MAX LENGTH %(limit_value)s",
        }
        f = EmailField(min_length=8, max_length=10, error_messages=e)
        self.assertFormErrors(["REQUIRED"], f.clean, "")
        self.assertFormErrors(["INVALID"], f.clean, "abcdefgh")
        self.assertFormErrors(["LENGTH 7, MIN LENGTH 8"], f.clean, "a@b.com")
        self.assertFormErrors(["LENGTH 11, MAX LENGTH 10"], f.clean, "aye@bee.com")