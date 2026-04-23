def test_inline_formsets_with_nullable_unique_together(self):
        # Test inline formsets where the inline-edited object has a
        # unique_together constraint with a nullable member

        AuthorBooksFormSet4 = inlineformset_factory(
            Author,
            BookWithOptionalAltEditor,
            can_delete=False,
            extra=2,
            fields="__all__",
        )
        author = Author.objects.create(pk=1, name="Charles Baudelaire")

        data = {
            # The number of forms rendered.
            "bookwithoptionalalteditor_set-TOTAL_FORMS": "2",
            # The number of forms with initial data.
            "bookwithoptionalalteditor_set-INITIAL_FORMS": "0",
            # The max number of forms.
            "bookwithoptionalalteditor_set-MAX_NUM_FORMS": "",
            "bookwithoptionalalteditor_set-0-author": "1",
            "bookwithoptionalalteditor_set-0-title": "Les Fleurs du Mal",
            "bookwithoptionalalteditor_set-1-author": "1",
            "bookwithoptionalalteditor_set-1-title": "Les Fleurs du Mal",
        }
        formset = AuthorBooksFormSet4(data, instance=author)
        self.assertTrue(formset.is_valid())

        saved = formset.save()
        self.assertEqual(len(saved), 2)
        book1, book2 = saved
        self.assertEqual(book1.author_id, 1)
        self.assertEqual(book1.title, "Les Fleurs du Mal")
        self.assertEqual(book2.author_id, 1)
        self.assertEqual(book2.title, "Les Fleurs du Mal")