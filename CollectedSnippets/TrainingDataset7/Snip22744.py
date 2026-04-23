def test_generic_ipaddressfield(self):
        e = {
            "required": "REQUIRED",
            "invalid": "INVALID IP ADDRESS",
        }
        f = GenericIPAddressField(error_messages=e)
        self.assertFormErrors(["REQUIRED"], f.clean, "")
        self.assertFormErrors(["INVALID IP ADDRESS"], f.clean, "127.0.0")