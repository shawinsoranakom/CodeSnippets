def test_forms_with_multiple_choice(self):
        # MultipleChoiceField is a special case, as its data is required to be
        # a list:
        class SongForm(Form):
            name = CharField()
            composers = MultipleChoiceField()

        f = SongForm(auto_id=False)
        self.assertHTMLEqual(
            str(f["composers"]),
            """<select multiple name="composers" required>
</select>""",
        )

        class SongForm(Form):
            name = CharField()
            composers = MultipleChoiceField(
                choices=[("J", "John Lennon"), ("P", "Paul McCartney")]
            )

        f = SongForm(auto_id=False)
        self.assertHTMLEqual(
            str(f["composers"]),
            """<select multiple name="composers" required>
<option value="J">John Lennon</option>
<option value="P">Paul McCartney</option>
</select>""",
        )
        f = SongForm({"name": "Yesterday", "composers": ["P"]}, auto_id=False)
        self.assertHTMLEqual(
            str(f["name"]), '<input type="text" name="name" value="Yesterday" required>'
        )
        self.assertHTMLEqual(
            str(f["composers"]),
            """<select multiple name="composers" required>
<option value="J">John Lennon</option>
<option value="P" selected>Paul McCartney</option>
</select>""",
        )
        f = SongForm()
        self.assertHTMLEqual(
            f.as_table(),
            '<tr><th><label for="id_name">Name:</label></th>'
            '<td><input type="text" name="name" required id="id_name"></td>'
            '</tr><tr><th><label for="id_composers">Composers:</label></th>'
            '<td><select name="composers" required id="id_composers" multiple>'
            '<option value="J">John Lennon</option>'
            '<option value="P">Paul McCartney</option>'
            "</select></td></tr>",
        )
        self.assertHTMLEqual(
            f.as_ul(),
            '<li><label for="id_name">Name:</label>'
            '<input type="text" name="name" required id="id_name"></li>'
            '<li><label for="id_composers">Composers:</label>'
            '<select name="composers" required id="id_composers" multiple>'
            '<option value="J">John Lennon</option>'
            '<option value="P">Paul McCartney</option>'
            "</select></li>",
        )
        self.assertHTMLEqual(
            f.as_p(),
            '<p><label for="id_name">Name:</label>'
            '<input type="text" name="name" required id="id_name"></p>'
            '<p><label for="id_composers">Composers:</label>'
            '<select name="composers" required id="id_composers" multiple>'
            '<option value="J">John Lennon</option>'
            '<option value="P">Paul McCartney</option>'
            "</select></p>",
        )
        self.assertHTMLEqual(
            f.render(f.template_name_div),
            '<div><label for="id_name">Name:</label><input type="text" name="name" '
            'required id="id_name"></div><div><label for="id_composers">Composers:'
            '</label><select name="composers" required id="id_composers" multiple>'
            '<option value="J">John Lennon</option><option value="P">Paul McCartney'
            "</option></select></div>",
        )