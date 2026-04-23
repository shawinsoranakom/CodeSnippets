def test_charfield(self):
        e = {
            "required": "REQUIRED",
            "min_length": "LENGTH %(show_value)s, MIN LENGTH %(limit_value)s",
            "max_length": "LENGTH %(show_value)s, MAX LENGTH %(limit_value)s",
        }
        f = CharField(min_length=5, max_length=10, error_messages=e)
        self.assertFormErrors(["REQUIRED"], f.clean, "")
        self.assertFormErrors(["LENGTH 4, MIN LENGTH 5"], f.clean, "1234")
        self.assertFormErrors(["LENGTH 11, MAX LENGTH 10"], f.clean, "12345678901")