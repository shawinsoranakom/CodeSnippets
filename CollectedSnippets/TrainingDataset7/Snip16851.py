def test_render_checked(self):
        storage_url = default_storage.url("")
        widget = widgets.AdminFileWidget()
        widget.checked = True
        self.assertHTMLEqual(
            widget.render("test", self.album.cover_art),
            f'<p class="file-upload">Currently: <a href="{storage_url}albums/'
            r'hybrid_theory.jpg">albums\hybrid_theory.jpg</a> '
            '<span class="clearable-file-input">'
            '<input type="checkbox" name="test-clear" id="test-clear_id" checked>'
            '<label for="test-clear_id">Clear</label></span><br>'
            'Change: <input type="file" name="test" checked></p>',
        )