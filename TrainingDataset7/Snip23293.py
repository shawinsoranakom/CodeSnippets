def test_constructor_attrs_with_type(self):
        attrs = {"type": "number"}
        widget = MyMultiWidget(widgets=(TextInput, TextInput()), attrs=attrs)
        self.check_html(
            widget,
            "code",
            ["1", "2"],
            html=(
                '<input type="number" value="1" name="code_0">'
                '<input type="number" value="2" name="code_1">'
            ),
        )
        widget = MyMultiWidget(
            widgets=(TextInput(attrs), TextInput(attrs)), attrs={"class": "bar"}
        )
        self.check_html(
            widget,
            "code",
            ["1", "2"],
            html=(
                '<input type="number" value="1" name="code_0" class="bar">'
                '<input type="number" value="2" name="code_1" class="bar">'
            ),
        )