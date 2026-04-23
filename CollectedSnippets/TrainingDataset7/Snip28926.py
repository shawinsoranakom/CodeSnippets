def test_missing_field(self):
        class TestModelAdmin(ModelAdmin):
            radio_fields = {"non_existent_field": VERTICAL}

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'radio_fields' refers to 'non_existent_field', "
            "which is not a field of 'modeladmin.ValidationTestModel'.",
            "admin.E022",
        )