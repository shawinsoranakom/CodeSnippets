def test_edit_only(self):
        charles = Author.objects.create(name="Charles Baudelaire")
        AuthorFormSet = modelformset_factory(Author, fields="__all__", edit_only=True)
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "0",
            "form-0-name": "Arthur Rimbaud",
            "form-1-name": "Walt Whitman",
        }
        formset = AuthorFormSet(data)
        self.assertIs(formset.is_valid(), True)
        formset.save()
        self.assertSequenceEqual(Author.objects.all(), [charles])
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "1",
            "form-MAX_NUM_FORMS": "0",
            "form-0-id": charles.pk,
            "form-0-name": "Arthur Rimbaud",
            "form-1-name": "Walt Whitman",
        }
        formset = AuthorFormSet(data)
        self.assertIs(formset.is_valid(), True)
        formset.save()
        charles.refresh_from_db()
        self.assertEqual(charles.name, "Arthur Rimbaud")
        self.assertSequenceEqual(Author.objects.all(), [charles])