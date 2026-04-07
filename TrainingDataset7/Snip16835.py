def test_render(self):
        # Backslash in verbose_name to ensure it is JavaScript escaped.
        w = widgets.FilteredSelectMultiple("test\\", False)
        self.assertHTMLEqual(
            w.render("test", "test"),
            '<select multiple name="test" class="selectfilter" '
            'data-field-name="test\\" data-is-stacked="0">\n</select>',
        )