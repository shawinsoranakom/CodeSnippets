def test_not_dictionary(self):
        class TestModelAdmin(ModelAdmin):
            prepopulated_fields = ()

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'prepopulated_fields' must be a dictionary.",
            "admin.E026",
        )