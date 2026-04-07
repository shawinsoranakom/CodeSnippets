def test_raw_id_many_to_many(self):
        self.assertFormfield(
            Band, "members", widgets.ManyToManyRawIdWidget, raw_id_fields=["members"]
        )