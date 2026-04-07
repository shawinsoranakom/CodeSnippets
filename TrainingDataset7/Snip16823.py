def test_inheritance(self):
        self.assertFormfield(Album, "backside_art", widgets.AdminFileWidget)