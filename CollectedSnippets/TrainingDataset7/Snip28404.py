def test_validate_foreign_key_uses_default_manager(self):
        class MyForm(forms.ModelForm):
            class Meta:
                model = Article
                fields = "__all__"

        # Archived writers are filtered out by the default manager.
        w = Writer.objects.create(name="Randy", archived=True)
        data = {
            "headline": "My Article",
            "slug": "my-article",
            "pub_date": datetime.date.today(),
            "writer": w.pk,
            "article": "lorem ipsum",
        }
        form = MyForm(data)
        self.assertIs(form.is_valid(), False)
        self.assertEqual(
            form.errors,
            {
                "writer": [
                    "Select a valid choice. That choice is not one of the available "
                    "choices."
                ]
            },
        )