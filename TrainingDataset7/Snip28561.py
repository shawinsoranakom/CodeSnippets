def test_prevent_duplicates_from_with_the_same_formset(self):
        FormSet = modelformset_factory(Product, fields="__all__", extra=2)
        data = {
            "form-TOTAL_FORMS": 2,
            "form-INITIAL_FORMS": 0,
            "form-MAX_NUM_FORMS": "",
            "form-0-slug": "red_car",
            "form-1-slug": "red_car",
        }
        formset = FormSet(data)
        self.assertFalse(formset.is_valid())
        self.assertEqual(
            formset._non_form_errors, ["Please correct the duplicate data for slug."]
        )

        FormSet = modelformset_factory(Price, fields="__all__", extra=2)
        data = {
            "form-TOTAL_FORMS": 2,
            "form-INITIAL_FORMS": 0,
            "form-MAX_NUM_FORMS": "",
            "form-0-price": "25",
            "form-0-quantity": "7",
            "form-1-price": "25",
            "form-1-quantity": "7",
        }
        formset = FormSet(data)
        self.assertFalse(formset.is_valid())
        self.assertEqual(
            formset._non_form_errors,
            [
                "Please correct the duplicate data for price and quantity, which must "
                "be unique."
            ],
        )

        # Only the price field is specified, this should skip any unique
        # checks since the unique_together is not fulfilled. This will fail
        # with a KeyError if broken.
        FormSet = modelformset_factory(Price, fields=("price",), extra=2)
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "",
            "form-0-price": "24",
            "form-1-price": "24",
        }
        formset = FormSet(data)
        self.assertTrue(formset.is_valid())

        FormSet = inlineformset_factory(Author, Book, extra=0, fields="__all__")
        author = Author.objects.create(pk=1, name="Charles Baudelaire")
        Book.objects.create(pk=1, author=author, title="Les Paradis Artificiels")
        Book.objects.create(pk=2, author=author, title="Les Fleurs du Mal")
        Book.objects.create(pk=3, author=author, title="Flowers of Evil")

        book_ids = author.book_set.order_by("id").values_list("id", flat=True)
        data = {
            "book_set-TOTAL_FORMS": "2",
            "book_set-INITIAL_FORMS": "2",
            "book_set-MAX_NUM_FORMS": "",
            "book_set-0-title": "The 2008 Election",
            "book_set-0-author": str(author.id),
            "book_set-0-id": str(book_ids[0]),
            "book_set-1-title": "The 2008 Election",
            "book_set-1-author": str(author.id),
            "book_set-1-id": str(book_ids[1]),
        }
        formset = FormSet(data=data, instance=author)
        self.assertFalse(formset.is_valid())
        self.assertEqual(
            formset._non_form_errors, ["Please correct the duplicate data for title."]
        )
        self.assertEqual(
            formset.errors,
            [{}, {"__all__": ["Please correct the duplicate values below."]}],
        )

        FormSet = modelformset_factory(Post, fields="__all__", extra=2)
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "",
            "form-0-title": "blah",
            "form-0-slug": "Morning",
            "form-0-subtitle": "foo",
            "form-0-posted": "2009-01-01",
            "form-1-title": "blah",
            "form-1-slug": "Morning in Prague",
            "form-1-subtitle": "rawr",
            "form-1-posted": "2009-01-01",
        }
        formset = FormSet(data)
        self.assertFalse(formset.is_valid())
        self.assertEqual(
            formset._non_form_errors,
            [
                "Please correct the duplicate data for title which must be unique for "
                "the date in posted."
            ],
        )
        self.assertEqual(
            formset.errors,
            [{}, {"__all__": ["Please correct the duplicate values below."]}],
        )

        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "",
            "form-0-title": "foo",
            "form-0-slug": "Morning in Prague",
            "form-0-subtitle": "foo",
            "form-0-posted": "2009-01-01",
            "form-1-title": "blah",
            "form-1-slug": "Morning in Prague",
            "form-1-subtitle": "rawr",
            "form-1-posted": "2009-08-02",
        }
        formset = FormSet(data)
        self.assertFalse(formset.is_valid())
        self.assertEqual(
            formset._non_form_errors,
            [
                "Please correct the duplicate data for slug which must be unique for "
                "the year in posted."
            ],
        )

        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "",
            "form-0-title": "foo",
            "form-0-slug": "Morning in Prague",
            "form-0-subtitle": "rawr",
            "form-0-posted": "2008-08-01",
            "form-1-title": "blah",
            "form-1-slug": "Prague",
            "form-1-subtitle": "rawr",
            "form-1-posted": "2009-08-02",
        }
        formset = FormSet(data)
        self.assertFalse(formset.is_valid())
        self.assertEqual(
            formset._non_form_errors,
            [
                "Please correct the duplicate data for subtitle which must be unique "
                "for the month in posted."
            ],
        )