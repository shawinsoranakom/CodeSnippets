def test_both_list_editable_and_list_display_links(self):
        class ProductAdmin(ModelAdmin):
            list_editable = ("name",)
            list_display = ("name",)
            list_display_links = ("name",)

        self.assertIsInvalid(
            ProductAdmin,
            ValidationTestModel,
            "The value of 'name' cannot be in both 'list_editable' and "
            "'list_display_links'.",
            id="admin.E123",
        )