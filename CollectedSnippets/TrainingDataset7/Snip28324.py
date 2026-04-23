def test_blank_foreign_key_with_radio(self):
        class BookForm(forms.ModelForm):
            class Meta:
                model = Book
                fields = ["author"]
                widgets = {"author": forms.RadioSelect()}

        writer = Writer.objects.create(name="Joe Doe")
        form = BookForm()
        self.assertEqual(
            list(form.fields["author"].choices),
            [
                ("", "---------"),
                (writer.pk, "Joe Doe"),
            ],
        )