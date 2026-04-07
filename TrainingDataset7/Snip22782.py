def test_multiple_choice_list_data(self):
        # Data for a MultipleChoiceField should be a list. QueryDict and
        # MultiValueDict conveniently work with this.
        class SongForm(Form):
            name = CharField()
            composers = MultipleChoiceField(
                choices=[("J", "John Lennon"), ("P", "Paul McCartney")],
                widget=CheckboxSelectMultiple,
            )

        data = {"name": "Yesterday", "composers": ["J", "P"]}
        f = SongForm(data)
        self.assertEqual(f.errors, {})

        data = QueryDict("name=Yesterday&composers=J&composers=P")
        f = SongForm(data)
        self.assertEqual(f.errors, {})

        data = MultiValueDict({"name": ["Yesterday"], "composers": ["J", "P"]})
        f = SongForm(data)
        self.assertEqual(f.errors, {})

        # SelectMultiple uses ducktyping so that MultiValueDictLike.getlist()
        # is called.
        f = SongForm(MultiValueDictLike({"name": "Yesterday", "composers": "J"}))
        self.assertEqual(f.errors, {})
        self.assertEqual(f.cleaned_data["composers"], ["J"])