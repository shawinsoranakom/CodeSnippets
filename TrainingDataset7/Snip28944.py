def test_valid_case(self):
        @admin.display
        def a_callable(obj):
            pass

        class TestModelAdmin(ModelAdmin):
            @admin.display
            def a_method(self, obj):
                pass

            list_display = ("name", "decade_published_in", "a_method", a_callable)

        self.assertIsValid(TestModelAdmin, ValidationTestModel)