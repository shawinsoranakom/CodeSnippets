def test_assignment_of_none_null_false(self):
        class AuthorForm(forms.ModelForm):
            class Meta:
                model = Author1
                fields = ["publication", "full_name"]

        publication = Publication.objects.create(
            title="Pravda", date_published=datetime.date(1991, 8, 22)
        )
        author = Author1.objects.create(publication=publication, full_name="John Doe")
        form = AuthorForm({"publication": "", "full_name": "John Doe"}, instance=author)
        self.assertFalse(form.is_valid())