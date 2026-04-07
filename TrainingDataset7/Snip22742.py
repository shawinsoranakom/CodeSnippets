def test_multiplechoicefield(self):
        e = {
            "required": "REQUIRED",
            "invalid_choice": "%(value)s IS INVALID CHOICE",
            "invalid_list": "NOT A LIST",
        }
        f = MultipleChoiceField(choices=[("a", "aye")], error_messages=e)
        self.assertFormErrors(["REQUIRED"], f.clean, "")
        self.assertFormErrors(["NOT A LIST"], f.clean, "b")
        self.assertFormErrors(["b IS INVALID CHOICE"], f.clean, ["b"])