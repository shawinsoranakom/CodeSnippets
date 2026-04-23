def test_modelchoicefield(self):
        # Create choices for the model choice field tests below.
        ChoiceModel.objects.create(pk=1, name="a")
        ChoiceModel.objects.create(pk=2, name="b")
        ChoiceModel.objects.create(pk=3, name="c")

        # ModelChoiceField
        e = {
            "required": "REQUIRED",
            "invalid_choice": "INVALID CHOICE",
        }
        f = ModelChoiceField(queryset=ChoiceModel.objects.all(), error_messages=e)
        self.assertFormErrors(["REQUIRED"], f.clean, "")
        self.assertFormErrors(["INVALID CHOICE"], f.clean, "4")

        # ModelMultipleChoiceField
        e = {
            "required": "REQUIRED",
            "invalid_choice": "%(value)s IS INVALID CHOICE",
            "invalid_list": "NOT A LIST OF VALUES",
        }
        f = ModelMultipleChoiceField(
            queryset=ChoiceModel.objects.all(), error_messages=e
        )
        self.assertFormErrors(["REQUIRED"], f.clean, "")
        self.assertFormErrors(["NOT A LIST OF VALUES"], f.clean, "3")
        self.assertFormErrors(["4 IS INVALID CHOICE"], f.clean, ["4"])