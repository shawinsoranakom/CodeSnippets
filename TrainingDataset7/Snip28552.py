def test_inlineformset_with_arrayfield(self):
        class SimpleArrayField(forms.CharField):
            """A proxy for django.contrib.postgres.forms.SimpleArrayField."""

            def to_python(self, value):
                value = super().to_python(value)
                return value.split(",") if value else []

        class BookForm(forms.ModelForm):
            title = SimpleArrayField()

            class Meta:
                model = Book
                fields = ["title"]

        BookFormSet = inlineformset_factory(Author, Book, form=BookForm)
        self.assertEqual(BookForm.Meta.fields, ["title"])
        data = {
            "book_set-TOTAL_FORMS": "3",
            "book_set-INITIAL_FORMS": "0",
            "book_set-MAX_NUM_FORMS": "",
            "book_set-0-title": "test1,test2",
            "book_set-1-title": "test1,test2",
            "book_set-2-title": "test3,test4",
        }
        author = Author.objects.create(name="test")
        formset = BookFormSet(data, instance=author)
        self.assertEqual(BookForm.Meta.fields, ["title"])
        self.assertEqual(
            formset.errors,
            [{}, {"__all__": ["Please correct the duplicate values below."]}, {}],
        )