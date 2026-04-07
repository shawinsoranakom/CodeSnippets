def test_list_display_first_item_in_list_editable_no_list_display_links(self):
        """
        The first item in list_display cannot be in list_editable if
        list_display_links isn't defined.
        """

        class ProductAdmin(ModelAdmin):
            list_display = ["name", "slug", "pub_date"]
            list_editable = ["slug", "name"]

        self.assertIsInvalid(
            ProductAdmin,
            ValidationTestModel,
            "The value of 'list_editable[1]' refers to the first field "
            "in 'list_display' ('name'), which cannot be used unless "
            "'list_display_links' is set.",
            id="admin.E124",
        )