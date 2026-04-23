def test_simple_save(self):
        qs = Author.objects.all()
        AuthorFormSet = modelformset_factory(Author, fields="__all__", extra=3)

        formset = AuthorFormSet(queryset=qs)
        self.assertEqual(len(formset.forms), 3)
        self.assertHTMLEqual(
            formset.forms[0].as_p(),
            '<p><label for="id_form-0-name">Name:</label>'
            '<input id="id_form-0-name" type="text" name="form-0-name" maxlength="100">'
            '<input type="hidden" name="form-0-id" id="id_form-0-id"></p>',
        )
        self.assertHTMLEqual(
            formset.forms[1].as_p(),
            '<p><label for="id_form-1-name">Name:</label>'
            '<input id="id_form-1-name" type="text" name="form-1-name" maxlength="100">'
            '<input type="hidden" name="form-1-id" id="id_form-1-id"></p>',
        )
        self.assertHTMLEqual(
            formset.forms[2].as_p(),
            '<p><label for="id_form-2-name">Name:</label>'
            '<input id="id_form-2-name" type="text" name="form-2-name" maxlength="100">'
            '<input type="hidden" name="form-2-id" id="id_form-2-id"></p>',
        )

        data = {
            "form-TOTAL_FORMS": "3",  # the number of forms rendered
            "form-INITIAL_FORMS": "0",  # the number of forms with initial data
            "form-MAX_NUM_FORMS": "",  # the max number of forms
            "form-0-name": "Charles Baudelaire",
            "form-1-name": "Arthur Rimbaud",
            "form-2-name": "",
        }

        formset = AuthorFormSet(data=data, queryset=qs)
        self.assertTrue(formset.is_valid())

        saved = formset.save()
        self.assertEqual(len(saved), 2)
        author1, author2 = saved
        self.assertEqual(author1, Author.objects.get(name="Charles Baudelaire"))
        self.assertEqual(author2, Author.objects.get(name="Arthur Rimbaud"))

        authors = list(Author.objects.order_by("name"))
        self.assertEqual(authors, [author2, author1])

        # Gah! We forgot Paul Verlaine. Let's create a formset to edit the
        # existing authors with an extra form to add him. We *could* pass in a
        # queryset to restrict the Author objects we edit, but in this case
        # we'll use it to display them in alphabetical order by name.

        qs = Author.objects.order_by("name")
        AuthorFormSet = modelformset_factory(
            Author, fields="__all__", extra=1, can_delete=False
        )

        formset = AuthorFormSet(queryset=qs)
        self.assertEqual(len(formset.forms), 3)
        self.assertHTMLEqual(
            formset.forms[0].as_p(),
            '<p><label for="id_form-0-name">Name:</label>'
            '<input id="id_form-0-name" type="text" name="form-0-name" '
            'value="Arthur Rimbaud" maxlength="100">'
            '<input type="hidden" name="form-0-id" value="%s" id="id_form-0-id"></p>'
            % author2.id,
        )
        self.assertHTMLEqual(
            formset.forms[1].as_p(),
            '<p><label for="id_form-1-name">Name:</label>'
            '<input id="id_form-1-name" type="text" name="form-1-name" '
            'value="Charles Baudelaire" maxlength="100">'
            '<input type="hidden" name="form-1-id" value="%s" id="id_form-1-id"></p>'
            % author1.id,
        )
        self.assertHTMLEqual(
            formset.forms[2].as_p(),
            '<p><label for="id_form-2-name">Name:</label>'
            '<input id="id_form-2-name" type="text" name="form-2-name" maxlength="100">'
            '<input type="hidden" name="form-2-id" id="id_form-2-id"></p>',
        )

        data = {
            "form-TOTAL_FORMS": "3",  # the number of forms rendered
            "form-INITIAL_FORMS": "2",  # the number of forms with initial data
            "form-MAX_NUM_FORMS": "",  # the max number of forms
            "form-0-id": str(author2.id),
            "form-0-name": "Arthur Rimbaud",
            "form-1-id": str(author1.id),
            "form-1-name": "Charles Baudelaire",
            "form-2-name": "Paul Verlaine",
        }

        formset = AuthorFormSet(data=data, queryset=qs)
        self.assertTrue(formset.is_valid())

        # Only changed or new objects are returned from formset.save()
        saved = formset.save()
        self.assertEqual(len(saved), 1)
        author3 = saved[0]
        self.assertEqual(author3, Author.objects.get(name="Paul Verlaine"))

        authors = list(Author.objects.order_by("name"))
        self.assertEqual(authors, [author2, author1, author3])

        # This probably shouldn't happen, but it will. If an add form was
        # marked for deletion, make sure we don't save that form.

        qs = Author.objects.order_by("name")
        AuthorFormSet = modelformset_factory(
            Author, fields="__all__", extra=1, can_delete=True
        )

        formset = AuthorFormSet(queryset=qs)
        self.assertEqual(len(formset.forms), 4)
        self.assertHTMLEqual(
            formset.forms[0].as_p(),
            '<p><label for="id_form-0-name">Name:</label>'
            '<input id="id_form-0-name" type="text" name="form-0-name" '
            'value="Arthur Rimbaud" maxlength="100"></p>'
            '<p><label for="id_form-0-DELETE">Delete:</label>'
            '<input type="checkbox" name="form-0-DELETE" id="id_form-0-DELETE">'
            '<input type="hidden" name="form-0-id" value="%s" id="id_form-0-id"></p>'
            % author2.id,
        )
        self.assertHTMLEqual(
            formset.forms[1].as_p(),
            '<p><label for="id_form-1-name">Name:</label>'
            '<input id="id_form-1-name" type="text" name="form-1-name" '
            'value="Charles Baudelaire" maxlength="100"></p>'
            '<p><label for="id_form-1-DELETE">Delete:</label>'
            '<input type="checkbox" name="form-1-DELETE" id="id_form-1-DELETE">'
            '<input type="hidden" name="form-1-id" value="%s" id="id_form-1-id"></p>'
            % author1.id,
        )
        self.assertHTMLEqual(
            formset.forms[2].as_p(),
            '<p><label for="id_form-2-name">Name:</label>'
            '<input id="id_form-2-name" type="text" name="form-2-name" '
            'value="Paul Verlaine" maxlength="100"></p>'
            '<p><label for="id_form-2-DELETE">Delete:</label>'
            '<input type="checkbox" name="form-2-DELETE" id="id_form-2-DELETE">'
            '<input type="hidden" name="form-2-id" value="%s" id="id_form-2-id"></p>'
            % author3.id,
        )
        self.assertHTMLEqual(
            formset.forms[3].as_p(),
            '<p><label for="id_form-3-name">Name:</label>'
            '<input id="id_form-3-name" type="text" name="form-3-name" maxlength="100">'
            '</p><p><label for="id_form-3-DELETE">Delete:</label>'
            '<input type="checkbox" name="form-3-DELETE" id="id_form-3-DELETE">'
            '<input type="hidden" name="form-3-id" id="id_form-3-id"></p>',
        )

        data = {
            "form-TOTAL_FORMS": "4",  # the number of forms rendered
            "form-INITIAL_FORMS": "3",  # the number of forms with initial data
            "form-MAX_NUM_FORMS": "",  # the max number of forms
            "form-0-id": str(author2.id),
            "form-0-name": "Arthur Rimbaud",
            "form-1-id": str(author1.id),
            "form-1-name": "Charles Baudelaire",
            "form-2-id": str(author3.id),
            "form-2-name": "Paul Verlaine",
            "form-3-name": "Walt Whitman",
            "form-3-DELETE": "on",
        }

        formset = AuthorFormSet(data=data, queryset=qs)
        self.assertTrue(formset.is_valid())

        # No objects were changed or saved so nothing will come back.

        self.assertEqual(formset.save(), [])

        authors = list(Author.objects.order_by("name"))
        self.assertEqual(authors, [author2, author1, author3])

        # Let's edit a record to ensure save only returns that one record.

        data = {
            "form-TOTAL_FORMS": "4",  # the number of forms rendered
            "form-INITIAL_FORMS": "3",  # the number of forms with initial data
            "form-MAX_NUM_FORMS": "",  # the max number of forms
            "form-0-id": str(author2.id),
            "form-0-name": "Walt Whitman",
            "form-1-id": str(author1.id),
            "form-1-name": "Charles Baudelaire",
            "form-2-id": str(author3.id),
            "form-2-name": "Paul Verlaine",
            "form-3-name": "",
            "form-3-DELETE": "",
        }

        formset = AuthorFormSet(data=data, queryset=qs)
        self.assertTrue(formset.is_valid())

        # One record has changed.

        saved = formset.save()
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0], Author.objects.get(name="Walt Whitman"))