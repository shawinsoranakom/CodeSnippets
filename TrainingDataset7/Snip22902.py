def test_renderer_custom_bound_field(self):
        t = Template("{{ form }}")
        html = t.render(Context({"form": Person()}))
        expected = """
            <div><label for="id_first_name">First name</label>
            <input type="text" name="first_name" required
            id="id_first_name"></div>
            <div><label for="id_last_name">Last name</label>
            <input type="text" name="last_name" required
            id="id_last_name"></div><div>
            <label for="id_birthday">Birthday</label>
            <input type="text" name="birthday" required
            id="id_birthday"></div>"""
        self.assertHTMLEqual(html, expected)