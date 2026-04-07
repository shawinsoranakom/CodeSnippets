def test_edit_only_formset_factory_with_basemodelformset(self):
        charles = Author.objects.create(name="Charles Baudelaire")

        class AuthorForm(forms.ModelForm):
            class Meta:
                model = Author
                fields = "__all__"

        class BaseAuthorFormSet(BaseModelFormSet):
            def __init__(self, *args, **kwargs):
                self.model = Author
                super().__init__(*args, **kwargs)

        AuthorFormSet = formset_factory(AuthorForm, formset=BaseAuthorFormSet)
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "1",
            "form-MAX_NUM_FORMS": "0",
            "form-0-id": charles.pk,
            "form-0-name": "Shawn Dong",
            "form-1-name": "Walt Whitman",
        }
        formset = AuthorFormSet(data)
        self.assertIs(formset.is_valid(), True)
        formset.save()
        self.assertEqual(Author.objects.count(), 2)
        charles.refresh_from_db()
        self.assertEqual(charles.name, "Shawn Dong")
        self.assertEqual(Author.objects.count(), 2)