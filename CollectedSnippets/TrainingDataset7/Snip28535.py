def test_inline_formsets_with_custom_pk(self):
        # Test inline formsets where the inline-edited object has a custom
        # primary key that is not the fk to the parent object.
        self.maxDiff = 1024

        AuthorBooksFormSet2 = inlineformset_factory(
            Author, BookWithCustomPK, can_delete=False, extra=1, fields="__all__"
        )
        author = Author.objects.create(pk=1, name="Charles Baudelaire")

        formset = AuthorBooksFormSet2(instance=author)
        self.assertEqual(len(formset.forms), 1)
        self.assertHTMLEqual(
            formset.forms[0].as_p(),
            '<p><label for="id_bookwithcustompk_set-0-my_pk">My pk:</label>'
            '<input id="id_bookwithcustompk_set-0-my_pk" type="number" '
            'name="bookwithcustompk_set-0-my_pk" step="1"></p>'
            '<p><label for="id_bookwithcustompk_set-0-title">Title:</label>'
            '<input id="id_bookwithcustompk_set-0-title" type="text" '
            'name="bookwithcustompk_set-0-title" maxlength="100">'
            '<input type="hidden" name="bookwithcustompk_set-0-author" '
            'value="1" id="id_bookwithcustompk_set-0-author"></p>',
        )

        data = {
            # The number of forms rendered.
            "bookwithcustompk_set-TOTAL_FORMS": "1",
            # The number of forms with initial data.
            "bookwithcustompk_set-INITIAL_FORMS": "0",
            # The max number of forms.
            "bookwithcustompk_set-MAX_NUM_FORMS": "",
            "bookwithcustompk_set-0-my_pk": "77777",
            "bookwithcustompk_set-0-title": "Les Fleurs du Mal",
        }

        formset = AuthorBooksFormSet2(data, instance=author)
        self.assertTrue(formset.is_valid())

        saved = formset.save()
        self.assertEqual(len(saved), 1)
        (book1,) = saved
        self.assertEqual(book1.pk, 77777)

        book1 = author.bookwithcustompk_set.get()
        self.assertEqual(book1.title, "Les Fleurs du Mal")