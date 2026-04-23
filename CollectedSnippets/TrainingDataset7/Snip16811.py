def test_radio_fields_ForeignKey(self):
        ff = self.assertFormfield(
            Event,
            "main_band",
            widgets.AdminRadioSelect,
            radio_fields={"main_band": admin.VERTICAL},
        )
        self.assertIsNone(ff.empty_label)