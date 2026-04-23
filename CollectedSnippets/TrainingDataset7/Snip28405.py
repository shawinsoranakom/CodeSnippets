def test_validate_foreign_key_to_model_with_overridden_manager(self):
        class MyForm(forms.ModelForm):
            class Meta:
                model = Article
                fields = "__all__"

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Allow archived authors.
                self.fields["writer"].queryset = Writer._base_manager.all()

        w = Writer.objects.create(name="Randy", archived=True)
        data = {
            "headline": "My Article",
            "slug": "my-article",
            "pub_date": datetime.date.today(),
            "writer": w.pk,
            "article": "lorem ipsum",
        }
        form = MyForm(data)
        self.assertIs(form.is_valid(), True)
        article = form.save()
        self.assertEqual(article.writer, w)