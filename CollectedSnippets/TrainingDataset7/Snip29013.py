def test_list_display_first_item_same_as_list_editable_first_item(self):
        """
        The first item in list_display can be the same as the first in
        list_editable.
        """

        class ProductAdmin(ModelAdmin):
            list_display = ["name", "slug", "pub_date"]
            list_editable = ["name", "slug"]
            list_display_links = ["pub_date"]

        self.assertIsValid(ProductAdmin, ValidationTestModel)