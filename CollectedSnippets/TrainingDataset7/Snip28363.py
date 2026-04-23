def test_label_overrides(self):
        form = FieldOverridesByFormMetaForm()
        self.assertHTMLEqual(
            str(form["name"].label_tag()),
            '<label for="id_name">Title:</label>',
        )
        self.assertHTMLEqual(
            str(form["url"].label_tag()),
            '<label for="id_url">The URL:</label>',
        )
        self.assertHTMLEqual(
            str(form["slug"].label_tag()),
            '<label for="id_slug">Slug:</label>',
        )
        self.assertHTMLEqual(
            form["name"].legend_tag(),
            "<legend>Title:</legend>",
        )
        self.assertHTMLEqual(
            form["url"].legend_tag(),
            "<legend>The URL:</legend>",
        )
        self.assertHTMLEqual(
            form["slug"].legend_tag(),
            "<legend>Slug:</legend>",
        )