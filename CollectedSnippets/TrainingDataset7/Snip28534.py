def test_inline_formsets_save_as_new(self):
        # The save_as_new parameter lets you re-associate the data to a new
        # instance. This is used in the admin for save_as functionality.
        AuthorBooksFormSet = inlineformset_factory(
            Author, Book, can_delete=False, extra=2, fields="__all__"
        )
        Author.objects.create(name="Charles Baudelaire")

        # An immutable QueryDict simulates request.POST.
        data = QueryDict(mutable=True)
        data.update(
            {
                "book_set-TOTAL_FORMS": "3",  # the number of forms rendered
                "book_set-INITIAL_FORMS": "2",  # the number of forms with initial data
                "book_set-MAX_NUM_FORMS": "",  # the max number of forms
                "book_set-0-id": "1",
                "book_set-0-title": "Les Fleurs du Mal",
                "book_set-1-id": "2",
                "book_set-1-title": "Les Paradis Artificiels",
                "book_set-2-title": "",
            }
        )
        data._mutable = False

        formset = AuthorBooksFormSet(data, instance=Author(), save_as_new=True)
        self.assertTrue(formset.is_valid())
        self.assertIs(data._mutable, False)

        new_author = Author.objects.create(name="Charles Baudelaire")
        formset = AuthorBooksFormSet(data, instance=new_author, save_as_new=True)
        saved = formset.save()
        self.assertEqual(len(saved), 2)
        book1, book2 = saved
        self.assertEqual(book1.title, "Les Fleurs du Mal")
        self.assertEqual(book2.title, "Les Paradis Artificiels")

        # Test using a custom prefix on an inline formset.

        formset = AuthorBooksFormSet(prefix="test")
        self.assertEqual(len(formset.forms), 2)
        self.assertHTMLEqual(
            formset.forms[0].as_p(),
            '<p><label for="id_test-0-title">Title:</label>'
            '<input id="id_test-0-title" type="text" name="test-0-title" '
            'maxlength="100">'
            '<input type="hidden" name="test-0-author" id="id_test-0-author">'
            '<input type="hidden" name="test-0-id" id="id_test-0-id"></p>',
        )

        self.assertHTMLEqual(
            formset.forms[1].as_p(),
            '<p><label for="id_test-1-title">Title:</label>'
            '<input id="id_test-1-title" type="text" name="test-1-title" '
            'maxlength="100">'
            '<input type="hidden" name="test-1-author" id="id_test-1-author">'
            '<input type="hidden" name="test-1-id" id="id_test-1-id"></p>',
        )