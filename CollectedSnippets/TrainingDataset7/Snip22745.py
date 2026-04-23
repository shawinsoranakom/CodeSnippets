def test_subclassing_errorlist(self):
        class TestForm(Form):
            first_name = CharField()
            last_name = CharField()
            birthday = DateField()

            def clean(self):
                raise ValidationError("I like to be awkward.")

        class CustomErrorList(utils.ErrorList):
            def __str__(self):
                return self.as_divs()

            def as_divs(self):
                if not self:
                    return ""
                return mark_safe(
                    '<div class="error">%s</div>'
                    % "".join("<p>%s</p>" % e for e in self)
                )

        # This form should print errors the default way.
        form1 = TestForm({"first_name": "John"})
        self.assertHTMLEqual(
            str(form1["last_name"].errors),
            '<ul class="errorlist" id="id_last_name_error"><li>'
            "This field is required.</li></ul>",
        )
        self.assertHTMLEqual(
            str(form1.errors["__all__"]),
            '<ul class="errorlist nonfield"><li>I like to be awkward.</li></ul>',
        )

        # This one should wrap error groups in the customized way.
        form2 = TestForm({"first_name": "John"}, error_class=CustomErrorList)
        self.assertHTMLEqual(
            str(form2["last_name"].errors),
            '<div class="error"><p>This field is required.</p></div>',
        )
        self.assertHTMLEqual(
            str(form2.errors["__all__"]),
            '<div class="error"><p>I like to be awkward.</p></div>',
        )