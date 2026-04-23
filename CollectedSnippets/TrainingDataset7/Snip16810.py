def test_raw_id_ForeignKey(self):
        self.assertFormfield(
            Event,
            "main_band",
            widgets.ForeignKeyRawIdWidget,
            raw_id_fields=["main_band"],
        )