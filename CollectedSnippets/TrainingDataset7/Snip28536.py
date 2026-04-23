def test_inline_formsets_with_multi_table_inheritance(self):
        # Test inline formsets where the inline-edited object uses multi-table
        # inheritance, thus has a non AutoField yet auto-created primary key.

        AuthorBooksFormSet3 = inlineformset_factory(
            Author, AlternateBook, can_delete=False, extra=1, fields="__all__"
        )
        author = Author.objects.create(pk=1, name="Charles Baudelaire")

        formset = AuthorBooksFormSet3(instance=author)
        self.assertEqual(len(formset.forms), 1)
        self.assertHTMLEqual(
            formset.forms[0].as_p(),
            '<p><label for="id_alternatebook_set-0-title">Title:</label>'
            '<input id="id_alternatebook_set-0-title" type="text" '
            'name="alternatebook_set-0-title" maxlength="100"></p>'
            '<p><label for="id_alternatebook_set-0-notes">Notes:</label>'
            '<input id="id_alternatebook_set-0-notes" type="text" '
            'name="alternatebook_set-0-notes" maxlength="100">'
            '<input type="hidden" name="alternatebook_set-0-author" value="1" '
            'id="id_alternatebook_set-0-author">'
            '<input type="hidden" name="alternatebook_set-0-book_ptr" '
            'id="id_alternatebook_set-0-book_ptr"></p>',
        )

        data = {
            # The number of forms rendered.
            "alternatebook_set-TOTAL_FORMS": "1",
            # The number of forms with initial data.
            "alternatebook_set-INITIAL_FORMS": "0",
            # The max number of forms.
            "alternatebook_set-MAX_NUM_FORMS": "",
            "alternatebook_set-0-title": "Flowers of Evil",
            "alternatebook_set-0-notes": "English translation of Les Fleurs du Mal",
        }

        formset = AuthorBooksFormSet3(data, instance=author)
        self.assertTrue(formset.is_valid())

        saved = formset.save()
        self.assertEqual(len(saved), 1)
        (book1,) = saved
        self.assertEqual(book1.title, "Flowers of Evil")
        self.assertEqual(book1.notes, "English translation of Les Fleurs du Mal")