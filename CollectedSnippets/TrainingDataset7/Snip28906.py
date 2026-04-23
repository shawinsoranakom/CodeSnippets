def test_duplicate_fields_in_fieldsets(self):
        class TestModelAdmin(ModelAdmin):
            fieldsets = [
                (None, {"fields": ["name"]}),
                (None, {"fields": ["name"]}),
            ]

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "There are duplicate field(s) in 'fieldsets[1][1]'.",
            "admin.E012",
            "Remove duplicates of 'name'.",
        )