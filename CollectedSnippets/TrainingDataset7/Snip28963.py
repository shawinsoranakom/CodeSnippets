def test_valid_case(self):
        class AwesomeFilter(SimpleListFilter):
            def get_title(self):
                return "awesomeness"

            def get_choices(self, request):
                return (("bit", "A bit awesome"), ("very", "Very awesome"))

            def get_queryset(self, cl, qs):
                return qs

        class TestModelAdmin(ModelAdmin):
            list_filter = (
                "is_active",
                AwesomeFilter,
                ("is_active", BooleanFieldListFilter),
                "no",
            )

        self.assertIsValid(TestModelAdmin, ValidationTestModel)