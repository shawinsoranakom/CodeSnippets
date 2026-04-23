def test_render_datetime(self):
        self.assertHTMLEqual(
            self.widget.render("mydate", date(2010, 4, 15)),
            self.widget.render("mydate", "2010-04-15"),
        )