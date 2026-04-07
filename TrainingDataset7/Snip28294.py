def test_disabled_modelchoicefield(self):
        class ModelChoiceForm(forms.ModelForm):
            author = forms.ModelChoiceField(Author.objects.all(), disabled=True)

            class Meta:
                model = Book
                fields = ["author"]

        book = Book.objects.create(author=Writer.objects.create(name="Test writer"))
        form = ModelChoiceForm({}, instance=book)
        self.assertEqual(
            form.errors["author"],
            ["Select a valid choice. That choice is not one of the available choices."],
        )