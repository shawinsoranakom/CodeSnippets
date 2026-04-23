def test_text_inputs(self):
        widget = MyMultiWidget(
            widgets=(
                TextInput(attrs={"class": "big"}),
                TextInput(attrs={"class": "small"}),
            )
        )
        self.check_html(
            widget,
            "name",
            ["john", "lennon"],
            html=(
                '<input type="text" class="big" value="john" name="name_0">'
                '<input type="text" class="small" value="lennon" name="name_1">'
            ),
        )
        self.check_html(
            widget,
            "name",
            ("john", "lennon"),
            html=(
                '<input type="text" class="big" value="john" name="name_0">'
                '<input type="text" class="small" value="lennon" name="name_1">'
            ),
        )
        self.check_html(
            widget,
            "name",
            "john__lennon",
            html=(
                '<input type="text" class="big" value="john" name="name_0">'
                '<input type="text" class="small" value="lennon" name="name_1">'
            ),
        )
        self.check_html(
            widget,
            "name",
            "john__lennon",
            attrs={"id": "foo"},
            html=(
                '<input id="foo_0" type="text" class="big" value="john" name="name_0">'
                '<input id="foo_1" type="text" class="small" value="lennon" '
                'name="name_1">'
            ),
        )