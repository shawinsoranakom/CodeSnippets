def test_iterate_checkboxes(self):
        f = SongForm({"composers": ["J", "P"]}, auto_id=False)
        t = Template(
            "{% for checkbox in form.composers %}"
            '<div class="mycheckbox">{{ checkbox }}</div>'
            "{% endfor %}"
        )
        self.assertHTMLEqual(
            t.render(Context({"form": f})),
            '<div class="mycheckbox"><label>'
            '<input checked name="composers" type="checkbox" value="J"> '
            "John Lennon</label></div>"
            '<div class="mycheckbox"><label>'
            '<input checked name="composers" type="checkbox" value="P"> '
            "Paul McCartney</label></div>",
        )