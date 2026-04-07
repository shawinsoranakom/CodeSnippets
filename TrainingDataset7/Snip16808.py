def test_FileField(self):
        self.assertFormfield(Album, "cover_art", widgets.AdminFileWidget)