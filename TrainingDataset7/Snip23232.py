def test_render_checked(self):
        self.widget.checked = True
        self.check_html(
            self.widget,
            "myfile",
            FakeFieldFile(),
            html=(
                'Currently: <a href="something">something</a>'
                '<input type="checkbox" name="myfile-clear" id="myfile-clear_id" '
                "checked>"
                '<label for="myfile-clear_id">Clear</label><br>Change: '
                '<input type="file" name="myfile" checked>'
            ),
        )