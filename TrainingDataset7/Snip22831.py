def test_extracting_hidden_and_visible(self):
        class SongForm(Form):
            token = CharField(widget=HiddenInput)
            artist = CharField()
            name = CharField()

        form = SongForm()
        self.assertEqual([f.name for f in form.hidden_fields()], ["token"])
        self.assertEqual([f.name for f in form.visible_fields()], ["artist", "name"])