def test_multivalue_optional_subfields_rendering(self):
        class PhoneWidget(MultiWidget):
            def __init__(self, attrs=None):
                widgets = [TextInput(), TextInput()]
                super().__init__(widgets, attrs)

            def decompress(self, value):
                return [None, None]

        class PhoneField(MultiValueField):
            def __init__(self, *args, **kwargs):
                fields = [CharField(), CharField(required=False)]
                super().__init__(fields, *args, **kwargs)

        class PhoneForm(Form):
            phone1 = PhoneField(widget=PhoneWidget)
            phone2 = PhoneField(widget=PhoneWidget, required=False)
            phone3 = PhoneField(widget=PhoneWidget, require_all_fields=False)
            phone4 = PhoneField(
                widget=PhoneWidget,
                required=False,
                require_all_fields=False,
            )

        form = PhoneForm(auto_id=False)
        self.assertHTMLEqual(
            form.as_p(),
            """
            <p>Phone1:<input type="text" name="phone1_0" required>
            <input type="text" name="phone1_1" required></p>
            <p>Phone2:<input type="text" name="phone2_0">
            <input type="text" name="phone2_1"></p>
            <p>Phone3:<input type="text" name="phone3_0" required>
            <input type="text" name="phone3_1"></p>
            <p>Phone4:<input type="text" name="phone4_0">
            <input type="text" name="phone4_1"></p>
            """,
        )