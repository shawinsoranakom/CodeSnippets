def test_specified_both_fields_and_fieldsets(self):
        class TestModelAdmin(ModelAdmin):
            fieldsets = (("General", {"fields": ("name",)}),)
            fields = ["name"]

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "Both 'fieldsets' and 'fields' are specified.",
            "admin.E005",
        )