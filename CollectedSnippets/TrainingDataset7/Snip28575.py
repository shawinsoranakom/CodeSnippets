def test_inlineformset_factory_labels_overrides(self):
        BookFormSet = inlineformset_factory(
            Author, Book, fields="__all__", labels={"title": "Name"}
        )
        form = BookFormSet.form()
        self.assertHTMLEqual(
            form["title"].label_tag(), '<label for="id_title">Name:</label>'
        )
        self.assertHTMLEqual(
            form["title"].legend_tag(),
            "<legend>Name:</legend>",
        )