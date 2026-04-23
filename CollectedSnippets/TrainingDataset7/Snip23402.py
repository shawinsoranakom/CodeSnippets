def test_render(self):
        self.check_html(
            self.widget, "telephone", "", html='<input type="tel" name="telephone">'
        )