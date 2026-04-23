def test_missing_fields_key(self):
        class TestModelAdmin(ModelAdmin):
            fieldsets = (("General", {}),)

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'fieldsets[0][1]' must contain the key 'fields'.",
            "admin.E011",
        )

        class TestModelAdmin(ModelAdmin):
            fieldsets = (("General", {"fields": ("name",)}),)

        self.assertIsValid(TestModelAdmin, ValidationTestModel)