def test_mixmodel_form(self):
        class MixModelForm(BaseCategoryForm):
            """Don't allow more than one 'model' definition in the
            inheritance hierarchy. Technically, it would generate a valid
            form, but the fact that the resulting save method won't deal with
            multiple objects is likely to trip up people not familiar with the
            mechanics.
            """

            class Meta:
                model = Article
                fields = "__all__"

            # MixModelForm is now an Article-related thing, because
            # MixModelForm.Meta overrides BaseCategoryForm.Meta.

        self.assertEqual(
            list(MixModelForm.base_fields),
            [
                "headline",
                "slug",
                "pub_date",
                "writer",
                "article",
                "categories",
                "status",
            ],
        )