def test_render(self):
        w = widgets.AdminFileWidget()
        self.assertHTMLEqual(
            w.render("test", self.album.cover_art),
            '<p class="file-upload">Currently: <a href="%(STORAGE_URL)salbums/'
            r'hybrid_theory.jpg">albums\hybrid_theory.jpg</a> '
            '<span class="clearable-file-input">'
            '<input type="checkbox" name="test-clear" id="test-clear_id"> '
            '<label for="test-clear_id">Clear</label></span><br>'
            'Change: <input type="file" name="test"></p>'
            % {
                "STORAGE_URL": default_storage.url(""),
            },
        )
        self.assertHTMLEqual(
            w.render("test", SimpleUploadedFile("test", b"content")),
            '<input type="file" name="test">',
        )