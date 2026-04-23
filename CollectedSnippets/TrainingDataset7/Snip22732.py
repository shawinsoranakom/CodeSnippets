def test_decimalfield(self):
        e = {
            "required": "REQUIRED",
            "invalid": "INVALID",
            "min_value": "MIN VALUE IS %(limit_value)s",
            "max_value": "MAX VALUE IS %(limit_value)s",
            "max_digits": "MAX DIGITS IS %(max)s",
            "max_decimal_places": "MAX DP IS %(max)s",
            "max_whole_digits": "MAX DIGITS BEFORE DP IS %(max)s",
        }
        f = DecimalField(min_value=5, max_value=10, error_messages=e)
        self.assertFormErrors(["REQUIRED"], f.clean, "")
        self.assertFormErrors(["INVALID"], f.clean, "abc")
        self.assertFormErrors(["MIN VALUE IS 5"], f.clean, "4")
        self.assertFormErrors(["MAX VALUE IS 10"], f.clean, "11")

        f2 = DecimalField(max_digits=4, decimal_places=2, error_messages=e)
        self.assertFormErrors(["MAX DIGITS IS 4"], f2.clean, "123.45")
        self.assertFormErrors(["MAX DP IS 2"], f2.clean, "1.234")
        self.assertFormErrors(["MAX DIGITS BEFORE DP IS 2"], f2.clean, "123.4")