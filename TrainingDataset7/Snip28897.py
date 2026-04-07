def test_field_attname(self):
        class TestModelAdmin(ModelAdmin):
            raw_id_fields = ["band_id"]

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'raw_id_fields[0]' refers to 'band_id', which is "
            "not a field of 'modeladmin.ValidationTestModel'.",
            "admin.E002",
        )