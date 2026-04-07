def test_choicefield(self):
        e = {
            "required": "REQUIRED",
            "invalid_choice": "%(value)s IS INVALID CHOICE",
        }
        f = ChoiceField(choices=[("a", "aye")], error_messages=e)
        self.assertFormErrors(["REQUIRED"], f.clean, "")
        self.assertFormErrors(["b IS INVALID CHOICE"], f.clean, "b")