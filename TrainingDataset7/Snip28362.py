def test_widget_overrides(self):
        form = FieldOverridesByFormMetaForm()
        self.assertHTMLEqual(
            str(form["name"]),
            '<textarea id="id_name" rows="10" cols="40" name="name" maxlength="20" '
            "required></textarea>",
        )
        self.assertHTMLEqual(
            str(form["url"]),
            '<input id="id_url" type="text" class="url" name="url" maxlength="40" '
            "required>",
        )
        self.assertHTMLEqual(
            str(form["slug"]),
            '<input id="id_slug" type="text" name="slug" maxlength="20" '
            'aria-describedby="id_slug_helptext" required>',
        )