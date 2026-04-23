def test_choices_with_radio_fields(self):
        self.assertFormfield(
            Member,
            "gender",
            widgets.AdminRadioSelect,
            radio_fields={"gender": admin.VERTICAL},
        )