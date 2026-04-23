def test_inline_formsets_with_custom_save_method(self):
        AuthorBooksFormSet = inlineformset_factory(
            Author, Book, can_delete=False, extra=2, fields="__all__"
        )
        author = Author.objects.create(pk=1, name="Charles Baudelaire")
        book1 = Book.objects.create(
            pk=1, author=author, title="Les Paradis Artificiels"
        )
        book2 = Book.objects.create(pk=2, author=author, title="Les Fleurs du Mal")
        book3 = Book.objects.create(pk=3, author=author, title="Flowers of Evil")

        class PoemForm(forms.ModelForm):
            def save(self, commit=True):
                # change the name to "Brooklyn Bridge" just to be a jerk.
                poem = super().save(commit=False)
                poem.name = "Brooklyn Bridge"
                if commit:
                    poem.save()
                return poem

        PoemFormSet = inlineformset_factory(Poet, Poem, form=PoemForm, fields="__all__")

        data = {
            "poem_set-TOTAL_FORMS": "3",  # the number of forms rendered
            "poem_set-INITIAL_FORMS": "0",  # the number of forms with initial data
            "poem_set-MAX_NUM_FORMS": "",  # the max number of forms
            "poem_set-0-name": "The Cloud in Trousers",
            "poem_set-1-name": "I",
            "poem_set-2-name": "",
        }

        poet = Poet.objects.create(name="Vladimir Mayakovsky")
        formset = PoemFormSet(data=data, instance=poet)
        self.assertTrue(formset.is_valid())

        saved = formset.save()
        self.assertEqual(len(saved), 2)
        poem1, poem2 = saved
        self.assertEqual(poem1.name, "Brooklyn Bridge")
        self.assertEqual(poem2.name, "Brooklyn Bridge")

        # We can provide a custom queryset to our InlineFormSet:

        custom_qs = Book.objects.order_by("-title")
        formset = AuthorBooksFormSet(instance=author, queryset=custom_qs)
        self.assertEqual(len(formset.forms), 5)
        self.assertHTMLEqual(
            formset.forms[0].as_p(),
            '<p><label for="id_book_set-0-title">Title:</label>'
            '<input id="id_book_set-0-title" type="text" name="book_set-0-title" '
            'value="Les Paradis Artificiels" maxlength="100">'
            '<input type="hidden" name="book_set-0-author" value="1" '
            'id="id_book_set-0-author">'
            '<input type="hidden" name="book_set-0-id" value="1" id="id_book_set-0-id">'
            "</p>",
        )
        self.assertHTMLEqual(
            formset.forms[1].as_p(),
            '<p><label for="id_book_set-1-title">Title:</label>'
            '<input id="id_book_set-1-title" type="text" name="book_set-1-title" '
            'value="Les Fleurs du Mal" maxlength="100">'
            '<input type="hidden" name="book_set-1-author" value="1" '
            'id="id_book_set-1-author">'
            '<input type="hidden" name="book_set-1-id" value="2" id="id_book_set-1-id">'
            "</p>",
        )
        self.assertHTMLEqual(
            formset.forms[2].as_p(),
            '<p><label for="id_book_set-2-title">Title:</label>'
            '<input id="id_book_set-2-title" type="text" name="book_set-2-title" '
            'value="Flowers of Evil" maxlength="100">'
            '<input type="hidden" name="book_set-2-author" value="1" '
            'id="id_book_set-2-author">'
            '<input type="hidden" name="book_set-2-id" value="3" '
            'id="id_book_set-2-id"></p>',
        )
        self.assertHTMLEqual(
            formset.forms[3].as_p(),
            '<p><label for="id_book_set-3-title">Title:</label>'
            '<input id="id_book_set-3-title" type="text" name="book_set-3-title" '
            'maxlength="100">'
            '<input type="hidden" name="book_set-3-author" value="1" '
            'id="id_book_set-3-author">'
            '<input type="hidden" name="book_set-3-id" id="id_book_set-3-id"></p>',
        )
        self.assertHTMLEqual(
            formset.forms[4].as_p(),
            '<p><label for="id_book_set-4-title">Title:</label>'
            '<input id="id_book_set-4-title" type="text" name="book_set-4-title" '
            'maxlength="100">'
            '<input type="hidden" name="book_set-4-author" value="1" '
            'id="id_book_set-4-author">'
            '<input type="hidden" name="book_set-4-id" id="id_book_set-4-id"></p>',
        )

        data = {
            "book_set-TOTAL_FORMS": "5",  # the number of forms rendered
            "book_set-INITIAL_FORMS": "3",  # the number of forms with initial data
            "book_set-MAX_NUM_FORMS": "",  # the max number of forms
            "book_set-0-id": str(book1.id),
            "book_set-0-title": "Les Paradis Artificiels",
            "book_set-1-id": str(book2.id),
            "book_set-1-title": "Les Fleurs du Mal",
            "book_set-2-id": str(book3.id),
            "book_set-2-title": "Flowers of Evil",
            "book_set-3-title": "Revue des deux mondes",
            "book_set-4-title": "",
        }
        formset = AuthorBooksFormSet(data, instance=author, queryset=custom_qs)
        self.assertTrue(formset.is_valid())

        custom_qs = Book.objects.filter(title__startswith="F")
        formset = AuthorBooksFormSet(instance=author, queryset=custom_qs)
        self.assertHTMLEqual(
            formset.forms[0].as_p(),
            '<p><label for="id_book_set-0-title">Title:</label>'
            '<input id="id_book_set-0-title" type="text" name="book_set-0-title" '
            'value="Flowers of Evil" maxlength="100">'
            '<input type="hidden" name="book_set-0-author" value="1" '
            'id="id_book_set-0-author">'
            '<input type="hidden" name="book_set-0-id" value="3" '
            'id="id_book_set-0-id"></p>',
        )
        self.assertHTMLEqual(
            formset.forms[1].as_p(),
            '<p><label for="id_book_set-1-title">Title:</label>'
            '<input id="id_book_set-1-title" type="text" name="book_set-1-title" '
            'maxlength="100">'
            '<input type="hidden" name="book_set-1-author" value="1" '
            'id="id_book_set-1-author">'
            '<input type="hidden" name="book_set-1-id" id="id_book_set-1-id"></p>',
        )
        self.assertHTMLEqual(
            formset.forms[2].as_p(),
            '<p><label for="id_book_set-2-title">Title:</label>'
            '<input id="id_book_set-2-title" type="text" name="book_set-2-title" '
            'maxlength="100">'
            '<input type="hidden" name="book_set-2-author" value="1" '
            'id="id_book_set-2-author">'
            '<input type="hidden" name="book_set-2-id" id="id_book_set-2-id"></p>',
        )

        data = {
            "book_set-TOTAL_FORMS": "3",  # the number of forms rendered
            "book_set-INITIAL_FORMS": "1",  # the number of forms with initial data
            "book_set-MAX_NUM_FORMS": "",  # the max number of forms
            "book_set-0-id": str(book3.id),
            "book_set-0-title": "Flowers of Evil",
            "book_set-1-title": "Revue des deux mondes",
            "book_set-2-title": "",
        }
        formset = AuthorBooksFormSet(data, instance=author, queryset=custom_qs)
        self.assertTrue(formset.is_valid())