def test_modelchoicefield_value_placeholder(self):
        f = ModelChoiceField(
            queryset=ChoiceModel.objects.all(),
            error_messages={
                "invalid_choice": '"%(value)s" is not one of the available choices.',
            },
        )
        self.assertFormErrors(
            ['"invalid" is not one of the available choices.'],
            f.clean,
            "invalid",
        )