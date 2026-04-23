def test_booleanfield(self):
        e = {
            "required": "REQUIRED",
        }
        f = BooleanField(error_messages=e)
        self.assertFormErrors(["REQUIRED"], f.clean, "")