def test_modelformset_factory_field_class_overrides(self):
        author = Author.objects.create(pk=1, name="Charles Baudelaire")
        BookFormSet = modelformset_factory(
            Book,
            fields="__all__",
            field_classes={
                "title": forms.SlugField,
            },
        )
        form = BookFormSet.form(data={"title": "Foo " * 30, "author": author.id})
        self.assertIs(Book._meta.get_field("title").__class__, models.CharField)
        self.assertIsInstance(form.fields["title"], forms.SlugField)