def test_timefield(self):
        e = {
            "required": "REQUIRED",
            "invalid": "INVALID",
        }
        f = TimeField(error_messages=e)
        self.assertFormErrors(["REQUIRED"], f.clean, "")
        self.assertFormErrors(["INVALID"], f.clean, "abc")