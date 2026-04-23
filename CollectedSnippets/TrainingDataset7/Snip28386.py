def test_override_unique_message(self):
        class CustomProductForm(ProductForm):
            class Meta(ProductForm.Meta):
                error_messages = {
                    "slug": {
                        "unique": "%(model_name)s's %(field_label)s not unique.",
                    }
                }

        Product.objects.create(slug="teddy-bear-blue")
        form = CustomProductForm({"slug": "teddy-bear-blue"})
        self.assertEqual(len(form.errors), 1)
        self.assertEqual(form.errors["slug"], ["Product's Slug not unique."])