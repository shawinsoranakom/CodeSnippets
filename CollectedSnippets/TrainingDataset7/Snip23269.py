def test_render(self):
        self.check_html(
            self.widget, "email", "", html='<input type="hidden" name="email">'
        )