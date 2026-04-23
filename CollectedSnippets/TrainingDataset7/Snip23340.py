def test_render(self):
        self.check_html(
            self.widget, "search", "", html='<input type="search" name="search">'
        )