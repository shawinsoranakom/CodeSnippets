def test_stacked_render(self):
        # Backslash in verbose_name to ensure it is JavaScript escaped.
        w = widgets.FilteredSelectMultiple("test\\", True)
        self.assertHTMLEqual(
            w.render("test", "test"),
            '<select multiple name="test" class="selectfilterstacked" '
            'data-field-name="test\\" data-is-stacked="1">\n</select>',
        )