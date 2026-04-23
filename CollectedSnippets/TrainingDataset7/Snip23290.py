def test_subwidgets_name(self):
        widget = MultiWidget(
            widgets={
                "": TextInput(),
                "big": TextInput(attrs={"class": "big"}),
                "small": TextInput(attrs={"class": "small"}),
            },
        )
        self.check_html(
            widget,
            "name",
            ["John", "George", "Paul"],
            html=(
                '<input type="text" name="name" value="John">'
                '<input type="text" name="name_big" value="George" class="big">'
                '<input type="text" name="name_small" value="Paul" class="small">'
            ),
        )