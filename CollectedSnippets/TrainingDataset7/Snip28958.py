def test_not_filter(self):
        class RandomClass:
            pass

        class TestModelAdmin(ModelAdmin):
            list_filter = (RandomClass,)

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'list_filter[0]' must inherit from 'ListFilter'.",
            "admin.E113",
        )