def test_disabled_multiplemodelchoicefield(self):
        class ArticleForm(forms.ModelForm):
            categories = forms.ModelMultipleChoiceField(
                Category.objects.all(), required=False
            )

            class Meta:
                model = Article
                fields = ["categories"]

        category1 = Category.objects.create(name="cat1")
        category2 = Category.objects.create(name="cat2")
        article = Article.objects.create(
            pub_date=datetime.date(1988, 1, 4),
            writer=Writer.objects.create(name="Test writer"),
        )
        article.categories.set([category1.pk])

        form = ArticleForm(data={"categories": [category2.pk]}, instance=article)
        self.assertEqual(form.errors, {})
        self.assertEqual(
            [x.pk for x in form.cleaned_data["categories"]], [category2.pk]
        )
        # Disabled fields use the value from `instance` rather than `data`.
        form = ArticleForm(data={"categories": [category2.pk]}, instance=article)
        form.fields["categories"].disabled = True
        self.assertEqual(form.errors, {})
        self.assertEqual(
            [x.pk for x in form.cleaned_data["categories"]], [category1.pk]
        )