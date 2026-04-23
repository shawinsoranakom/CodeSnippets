def test_list_display_link_checked_for_list_tuple_if_get_list_display_overridden(
        self,
    ):
        """
        list_display_links is checked for list/tuple/None even if
        get_list_display() is overridden.
        """

        class TestModelAdmin(ModelAdmin):
            list_display_links = "non-list/tuple"

            def get_list_display(self, request):
                pass

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'list_display_links' must be a list, a tuple, or None.",
            "admin.E110",
        )