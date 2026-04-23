def test_constructor_attrs(self):
        widget = MyMultiWidget(
            widgets=(
                TextInput(attrs={"class": "big"}),
                TextInput(attrs={"class": "small"}),
            ),
            attrs={"id": "bar"},
        )
        self.check_html(
            widget,
            "name",
            ["john", "lennon"],
            html=(
                '<input id="bar_0" type="text" class="big" value="john" name="name_0">'
                '<input id="bar_1" type="text" class="small" value="lennon" '
                'name="name_1">'
            ),
        )