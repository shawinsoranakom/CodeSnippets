def test_not_boolean(self):
        class TestModelAdmin(ModelAdmin):
            save_on_top = 1

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'save_on_top' must be a boolean.",
            "admin.E102",
        )