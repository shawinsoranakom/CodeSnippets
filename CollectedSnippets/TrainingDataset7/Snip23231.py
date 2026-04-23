def test_render_disabled(self):
        self.check_html(
            self.widget,
            "myfile",
            FakeFieldFile(),
            attrs={"disabled": True},
            html=(
                'Currently: <a href="something">something</a>'
                '<input type="checkbox" name="myfile-clear" '
                'id="myfile-clear_id" disabled>'
                '<label for="myfile-clear_id">Clear</label><br>'
                'Change: <input type="file" name="myfile" disabled>'
            ),
        )