def test_render(self):
        self.check_html(
            self.widget, "password", "", html='<input type="password" name="password">'
        )