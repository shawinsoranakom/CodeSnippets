def test_render_with_attrs_id(self):
        storage_url = default_storage.url("")
        w = widgets.AdminFileWidget()
        self.assertHTMLEqual(
            w.render("test", self.album.cover_art, attrs={"id": "test_id"}),
            f'<p class="file-upload">Currently: <a href="{storage_url}albums/'
            r'hybrid_theory.jpg">albums\hybrid_theory.jpg</a> '
            '<span class="clearable-file-input">'
            '<input type="checkbox" name="test-clear" id="test-clear_id"> '
            '<label for="test-clear_id">Clear</label></span><br>'
            'Change: <input type="file" name="test" id="test_id"></p>',
        )