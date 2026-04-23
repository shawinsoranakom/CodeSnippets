def test_inline_formsets(self):
        # We can also create a formset that is tied to a parent model. This is
        # how the admin system's edit inline functionality works.

        AuthorBooksFormSet = inlineformset_factory(
            Author, Book, can_delete=False, extra=3, fields="__all__"
        )
        author = Author.objects.create(name="Charles Baudelaire")

        formset = AuthorBooksFormSet(instance=author)
        self.assertEqual(len(formset.forms), 3)
        self.assertHTMLEqual(
            formset.forms[0].as_p(),
            '<p><label for="id_book_set-0-title">Title:</label>'
            '<input id="id_book_set-0-title" type="text" name="book_set-0-title" '
            'maxlength="100">'
            '<input type="hidden" name="book_set-0-author" value="%s" '
            'id="id_book_set-0-author">'
            '<input type="hidden" name="book_set-0-id" id="id_book_set-0-id">'
            "</p>" % author.id,
        )
        self.assertHTMLEqual(
            formset.forms[1].as_p(),
            '<p><label for="id_book_set-1-title">Title:</label>'
            '<input id="id_book_set-1-title" type="text" name="book_set-1-title" '
            'maxlength="100">'
            '<input type="hidden" name="book_set-1-author" value="%s" '
            'id="id_book_set-1-author">'
            '<input type="hidden" name="book_set-1-id" id="id_book_set-1-id"></p>'
            % author.id,
        )
        self.assertHTMLEqual(
            formset.forms[2].as_p(),
            '<p><label for="id_book_set-2-title">Title:</label>'
            '<input id="id_book_set-2-title" type="text" name="book_set-2-title" '
            'maxlength="100">'
            '<input type="hidden" name="book_set-2-author" value="%s" '
            'id="id_book_set-2-author">'
            '<input type="hidden" name="book_set-2-id" id="id_book_set-2-id"></p>'
            % author.id,
        )

        data = {
            "book_set-TOTAL_FORMS": "3",  # the number of forms rendered
            "book_set-INITIAL_FORMS": "0",  # the number of forms with initial data
            "book_set-MAX_NUM_FORMS": "",  # the max number of forms
            "book_set-0-title": "Les Fleurs du Mal",
            "book_set-1-title": "",
            "book_set-2-title": "",
        }

        formset = AuthorBooksFormSet(data, instance=author)
        self.assertTrue(formset.is_valid())

        saved = formset.save()
        self.assertEqual(len(saved), 1)
        (book1,) = saved
        self.assertEqual(book1, Book.objects.get(title="Les Fleurs du Mal"))
        self.assertSequenceEqual(author.book_set.all(), [book1])

        # Now that we've added a book to Charles Baudelaire, let's try adding
        # another one. This time though, an edit form will be available for
        # every existing book.

        AuthorBooksFormSet = inlineformset_factory(
            Author, Book, can_delete=False, extra=2, fields="__all__"
        )
        author = Author.objects.get(name="Charles Baudelaire")

        formset = AuthorBooksFormSet(instance=author)
        self.assertEqual(len(formset.forms), 3)
        self.assertHTMLEqual(
            formset.forms[0].as_p(),
            '<p><label for="id_book_set-0-title">Title:</label>'
            '<input id="id_book_set-0-title" type="text" name="book_set-0-title" '
            'value="Les Fleurs du Mal" maxlength="100">'
            '<input type="hidden" name="book_set-0-author" value="%s" '
            'id="id_book_set-0-author">'
            '<input type="hidden" name="book_set-0-id" value="%s" '
            'id="id_book_set-0-id"></p>'
            % (
                author.id,
                book1.id,
            ),
        )
        self.assertHTMLEqual(
            formset.forms[1].as_p(),
            '<p><label for="id_book_set-1-title">Title:</label>'
            '<input id="id_book_set-1-title" type="text" name="book_set-1-title" '
            'maxlength="100">'
            '<input type="hidden" name="book_set-1-author" value="%s" '
            'id="id_book_set-1-author">'
            '<input type="hidden" name="book_set-1-id" id="id_book_set-1-id"></p>'
            % author.id,
        )
        self.assertHTMLEqual(
            formset.forms[2].as_p(),
            '<p><label for="id_book_set-2-title">Title:</label>'
            '<input id="id_book_set-2-title" type="text" name="book_set-2-title" '
            'maxlength="100">'
            '<input type="hidden" name="book_set-2-author" value="%s" '
            'id="id_book_set-2-author">'
            '<input type="hidden" name="book_set-2-id" id="id_book_set-2-id"></p>'
            % author.id,
        )

        data = {
            "book_set-TOTAL_FORMS": "3",  # the number of forms rendered
            "book_set-INITIAL_FORMS": "1",  # the number of forms with initial data
            "book_set-MAX_NUM_FORMS": "",  # the max number of forms
            "book_set-0-id": str(book1.id),
            "book_set-0-title": "Les Fleurs du Mal",
            "book_set-1-title": "Les Paradis Artificiels",
            "book_set-2-title": "",
        }

        formset = AuthorBooksFormSet(data, instance=author)
        self.assertTrue(formset.is_valid())

        saved = formset.save()
        self.assertEqual(len(saved), 1)
        (book2,) = saved
        self.assertEqual(book2, Book.objects.get(title="Les Paradis Artificiels"))

        # As you can see, 'Les Paradis Artificiels' is now a book belonging to
        # Charles Baudelaire.
        self.assertSequenceEqual(author.book_set.order_by("title"), [book1, book2])