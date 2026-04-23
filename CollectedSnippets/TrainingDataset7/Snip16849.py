def test_render_required(self):
        widget = widgets.AdminFileWidget()
        widget.is_required = True
        self.assertHTMLEqual(
            widget.render("test", self.album.cover_art),
            '<p class="file-upload">Currently: <a href="%(STORAGE_URL)salbums/'
            r'hybrid_theory.jpg">albums\hybrid_theory.jpg</a><br>'
            'Change: <input type="file" name="test"></p>'
            % {
                "STORAGE_URL": default_storage.url(""),
            },
        )