def test_inlineformset_factory_widgets(self):
        widgets = {"title": forms.TextInput(attrs={"class": "book"})}
        BookFormSet = inlineformset_factory(
            Author, Book, widgets=widgets, fields="__all__"
        )
        form = BookFormSet.form()
        self.assertHTMLEqual(
            str(form["title"]),
            '<input class="book" id="id_title" maxlength="100" name="title" '
            'type="text" required>',
        )