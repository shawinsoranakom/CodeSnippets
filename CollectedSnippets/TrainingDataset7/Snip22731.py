def test_floatfield(self):
        e = {
            "required": "REQUIRED",
            "invalid": "INVALID",
            "min_value": "MIN VALUE IS %(limit_value)s",
            "max_value": "MAX VALUE IS %(limit_value)s",
        }
        f = FloatField(min_value=5, max_value=10, error_messages=e)
        self.assertFormErrors(["REQUIRED"], f.clean, "")
        self.assertFormErrors(["INVALID"], f.clean, "abc")
        self.assertFormErrors(["MIN VALUE IS 5"], f.clean, "4")
        self.assertFormErrors(["MAX VALUE IS 10"], f.clean, "11")