def test_hidden_data(self):
        class SongForm(Form):
            name = CharField()
            composers = MultipleChoiceField(
                choices=[("J", "John Lennon"), ("P", "Paul McCartney")]
            )

        # MultipleChoiceField rendered as_hidden() is a special case. Because
        # it can have multiple values, its as_hidden() renders multiple <input
        # type="hidden"> tags.
        f = SongForm({"name": "Yesterday", "composers": ["P"]}, auto_id=False)
        self.assertHTMLEqual(
            f["composers"].as_hidden(),
            '<input type="hidden" name="composers" value="P">',
        )
        f = SongForm({"name": "From Me To You", "composers": ["P", "J"]}, auto_id=False)
        self.assertHTMLEqual(
            f["composers"].as_hidden(),
            """<input type="hidden" name="composers" value="P">
<input type="hidden" name="composers" value="J">""",
        )

        # DateTimeField rendered as_hidden() is special too
        class MessageForm(Form):
            when = SplitDateTimeField()

        f = MessageForm({"when_0": "1992-01-01", "when_1": "01:01"})
        self.assertTrue(f.is_valid())
        self.assertHTMLEqual(
            str(f["when"]),
            '<input type="text" name="when_0" value="1992-01-01" id="id_when_0" '
            "required>"
            '<input type="text" name="when_1" value="01:01" id="id_when_1" required>',
        )
        self.assertHTMLEqual(
            f["when"].as_hidden(),
            '<input type="hidden" name="when_0" value="1992-01-01" id="id_when_0">'
            '<input type="hidden" name="when_1" value="01:01" id="id_when_1">',
        )