def test_assignment_of_none(self):
        class AuthorForm(forms.ModelForm):
            class Meta:
                model = Author
                fields = ["publication", "full_name"]

        publication = Publication.objects.create(
            title="Pravda", date_published=datetime.date(1991, 8, 22)
        )
        author = Author.objects.create(publication=publication, full_name="John Doe")
        form = AuthorForm({"publication": "", "full_name": "John Doe"}, instance=author)
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data["publication"])
        author = form.save()
        # author object returned from form still retains original publication
        # object that's why we need to retrieve it from database again
        new_author = Author.objects.get(pk=author.pk)
        self.assertIsNone(new_author.publication)