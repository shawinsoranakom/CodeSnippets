def test_not_boolean(self):
        class TestModelAdmin(ModelAdmin):
            save_as = 1

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'save_as' must be a boolean.",
            "admin.E101",
        )