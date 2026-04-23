def test_list_display_links_is_none(self):
        """
        list_display and list_editable can contain the same values
        when list_display_links is None
        """

        class ProductAdmin(ModelAdmin):
            list_display = ["name", "slug", "pub_date"]
            list_editable = list_display
            list_display_links = None

        self.assertIsValid(ProductAdmin, ValidationTestModel)