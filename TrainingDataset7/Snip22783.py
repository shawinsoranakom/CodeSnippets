def test_multiple_hidden(self):
        class SongForm(Form):
            name = CharField()
            composers = MultipleChoiceField(
                choices=[("J", "John Lennon"), ("P", "Paul McCartney")],
                widget=CheckboxSelectMultiple,
            )

        # The MultipleHiddenInput widget renders multiple values as hidden
        # fields.
        class SongFormHidden(Form):
            name = CharField()
            composers = MultipleChoiceField(
                choices=[("J", "John Lennon"), ("P", "Paul McCartney")],
                widget=MultipleHiddenInput,
            )

        f = SongFormHidden(
            MultiValueDict({"name": ["Yesterday"], "composers": ["J", "P"]}),
            auto_id=False,
        )
        self.assertHTMLEqual(
            f.as_ul(),
            """<li>Name: <input type="text" name="name" value="Yesterday" required>
<input type="hidden" name="composers" value="J">
<input type="hidden" name="composers" value="P"></li>""",
        )

        # When using CheckboxSelectMultiple, the framework expects a list of
        # input and returns a list of input.
        f = SongForm({"name": "Yesterday"}, auto_id=False)
        self.assertEqual(f.errors["composers"], ["This field is required."])
        f = SongForm({"name": "Yesterday", "composers": ["J"]}, auto_id=False)
        self.assertEqual(f.errors, {})
        self.assertEqual(f.cleaned_data["composers"], ["J"])
        self.assertEqual(f.cleaned_data["name"], "Yesterday")
        f = SongForm({"name": "Yesterday", "composers": ["J", "P"]}, auto_id=False)
        self.assertEqual(f.errors, {})
        self.assertEqual(f.cleaned_data["composers"], ["J", "P"])
        self.assertEqual(f.cleaned_data["name"], "Yesterday")

        # MultipleHiddenInput uses ducktyping so that
        # MultiValueDictLike.getlist() is called.
        f = SongForm(MultiValueDictLike({"name": "Yesterday", "composers": "J"}))
        self.assertEqual(f.errors, {})
        self.assertEqual(f.cleaned_data["composers"], ["J"])