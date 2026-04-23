def test_datefield(self):
        e = {
            "required": "REQUIRED",
            "invalid": "INVALID",
        }
        f = DateField(error_messages=e)
        self.assertFormErrors(["REQUIRED"], f.clean, "")
        self.assertFormErrors(["INVALID"], f.clean, "abc")