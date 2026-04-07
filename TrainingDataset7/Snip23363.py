def test_render_none(self):
        """
        Rendering the None or '' values should yield the same output.
        """
        self.assertHTMLEqual(
            self.widget.render("mydate", None),
            self.widget.render("mydate", ""),
        )