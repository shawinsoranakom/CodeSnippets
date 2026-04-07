def test_splitdatetimefield(self):
        e = {
            "required": "REQUIRED",
            "invalid_date": "INVALID DATE",
            "invalid_time": "INVALID TIME",
        }
        f = SplitDateTimeField(error_messages=e)
        self.assertFormErrors(["REQUIRED"], f.clean, "")
        self.assertFormErrors(["INVALID DATE", "INVALID TIME"], f.clean, ["a", "b"])