def test_list_filter_is_func(self):
        def get_filter():
            pass

        class TestModelAdmin(ModelAdmin):
            list_filter = [get_filter]

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'list_filter[0]' must inherit from 'ListFilter'.",
            "admin.E113",
        )