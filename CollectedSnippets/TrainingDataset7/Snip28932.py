def test_missing_field(self):
        class TestModelAdmin(ModelAdmin):
            prepopulated_fields = {"non_existent_field": ("slug",)}

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'prepopulated_fields' refers to 'non_existent_field', "
            "which is not a field of 'modeladmin.ValidationTestModel'.",
            "admin.E027",
        )