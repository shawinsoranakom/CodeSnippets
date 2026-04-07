def test_inlineformset_with_jsonfield(self):
        class BookForm(forms.ModelForm):
            title = forms.JSONField()

            class Meta:
                model = Book
                fields = ("title",)

        BookFormSet = inlineformset_factory(Author, Book, form=BookForm)
        data = {
            "book_set-TOTAL_FORMS": "3",
            "book_set-INITIAL_FORMS": "0",
            "book_set-MAX_NUM_FORMS": "",
            "book_set-0-title": {"test1": "test2"},
            "book_set-1-title": {"test1": "test2"},
            "book_set-2-title": {"test3": "test4"},
        }
        author = Author.objects.create(name="test")
        formset = BookFormSet(data, instance=author)
        self.assertEqual(
            formset.errors,
            [{}, {"__all__": ["Please correct the duplicate values below."]}, {}],
        )