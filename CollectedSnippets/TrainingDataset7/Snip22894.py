def test_errorlist_override(self):
        class CustomErrorList(ErrorList):
            template_name = "forms_tests/error.html"

        class CommentForm(Form):
            name = CharField(max_length=50, required=False)
            email = EmailField()
            comment = CharField()

        data = {"email": "invalid"}
        f = CommentForm(data, auto_id=False, error_class=CustomErrorList)
        self.assertHTMLEqual(
            f.as_p(),
            '<p>Name: <input type="text" name="name" maxlength="50"></p>'
            '<div class="errorlist">'
            '<div class="error">Enter a valid email address.</div></div>'
            "<p>Email: "
            '<input type="email" name="email" value="invalid" maxlength="320" '
            'aria-invalid="true" required></p><div class="errorlist">'
            '<div class="error">This field is required.</div></div>'
            '<p>Comment: <input type="text" name="comment" aria-invalid="true" '
            "required></p>",
        )