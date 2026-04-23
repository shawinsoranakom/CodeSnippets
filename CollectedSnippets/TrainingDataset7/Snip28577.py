def test_inlineformset_factory_help_text_overrides(self):
        BookFormSet = inlineformset_factory(
            Author, Book, fields="__all__", help_texts={"title": "Choose carefully."}
        )
        form = BookFormSet.form()
        self.assertEqual(form["title"].help_text, "Choose carefully.")