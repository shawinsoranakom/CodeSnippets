def test_to_field_name_with_initial_data(self):
        class ArticleCategoriesForm(forms.ModelForm):
            categories = forms.ModelMultipleChoiceField(
                Category.objects.all(), to_field_name="slug"
            )

            class Meta:
                model = Article
                fields = ["categories"]

        article = Article.objects.create(
            headline="Test article",
            slug="test-article",
            pub_date=datetime.date(1988, 1, 4),
            writer=Writer.objects.create(name="Test writer"),
            article="Hello.",
        )
        article.categories.add(self.c2, self.c3)
        form = ArticleCategoriesForm(instance=article)
        self.assertCountEqual(form["categories"].value(), [self.c2.slug, self.c3.slug])