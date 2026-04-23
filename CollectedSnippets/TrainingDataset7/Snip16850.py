def test_render_disabled(self):
        widget = widgets.AdminFileWidget(attrs={"disabled": True})
        self.assertHTMLEqual(
            widget.render("test", self.album.cover_art),
            '<p class="file-upload">Currently: <a href="%(STORAGE_URL)salbums/'
            r'hybrid_theory.jpg">albums\hybrid_theory.jpg</a> '
            '<span class="clearable-file-input">'
            '<input type="checkbox" name="test-clear" id="test-clear_id" disabled>'
            '<label for="test-clear_id">Clear</label></span><br>'
            'Change: <input type="file" name="test" disabled></p>'
            % {
                "STORAGE_URL": default_storage.url(""),
            },
        )