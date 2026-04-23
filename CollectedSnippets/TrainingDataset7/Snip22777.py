def test_multiple_checkbox_render(self):
        f = SongForm()
        self.assertHTMLEqual(
            f.as_table(),
            '<tr><th><label for="id_name">Name:</label></th><td>'
            '<input type="text" name="name" required id="id_name"></td></tr>'
            '<tr><th><label>Composers:</label></th><td><div id="id_composers">'
            '<div><label for="id_composers_0">'
            '<input type="checkbox" name="composers" value="J" '
            'id="id_composers_0">John Lennon</label></div>'
            '<div><label for="id_composers_1">'
            '<input type="checkbox" name="composers" value="P" '
            'id="id_composers_1">Paul McCartney</label></div>'
            "</div></td></tr>",
        )
        self.assertHTMLEqual(
            f.as_ul(),
            '<li><label for="id_name">Name:</label>'
            '<input type="text" name="name" required id="id_name"></li>'
            '<li><label>Composers:</label><div id="id_composers">'
            '<div><label for="id_composers_0">'
            '<input type="checkbox" name="composers" value="J" '
            'id="id_composers_0">John Lennon</label></div>'
            '<div><label for="id_composers_1">'
            '<input type="checkbox" name="composers" value="P" '
            'id="id_composers_1">Paul McCartney</label></div>'
            "</div></li>",
        )
        self.assertHTMLEqual(
            f.as_p(),
            '<p><label for="id_name">Name:</label>'
            '<input type="text" name="name" required id="id_name"></p>'
            '<p><label>Composers:</label><div id="id_composers">'
            '<div><label for="id_composers_0">'
            '<input type="checkbox" name="composers" value="J" '
            'id="id_composers_0">John Lennon</label></div>'
            '<div><label for="id_composers_1">'
            '<input type="checkbox" name="composers" value="P" '
            'id="id_composers_1">Paul McCartney</label></div>'
            "</div></p>",
        )
        self.assertHTMLEqual(
            f.render(f.template_name_div),
            '<div><label for="id_name">Name:</label><input type="text" name="name" '
            'required id="id_name"></div><div><fieldset><legend>Composers:</legend>'
            '<div id="id_composers"><div><label for="id_composers_0"><input '
            'type="checkbox" name="composers" value="J" id="id_composers_0">'
            'John Lennon</label></div><div><label for="id_composers_1"><input '
            'type="checkbox" name="composers" value="P" id="id_composers_1">'
            "Paul McCartney</label></div></div></fieldset></div>",
        )