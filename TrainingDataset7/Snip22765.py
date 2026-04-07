def test_various_boolean_values(self):
        class SignupForm(Form):
            email = EmailField()
            get_spam = BooleanField()

        f = SignupForm(auto_id=False)
        self.assertHTMLEqual(
            str(f["email"]),
            '<input type="email" name="email" maxlength="320" required>',
        )
        self.assertHTMLEqual(
            str(f["get_spam"]), '<input type="checkbox" name="get_spam" required>'
        )

        f = SignupForm({"email": "test@example.com", "get_spam": True}, auto_id=False)
        self.assertHTMLEqual(
            str(f["email"]),
            '<input type="email" name="email" maxlength="320" value="test@example.com" '
            "required>",
        )
        self.assertHTMLEqual(
            str(f["get_spam"]),
            '<input checked type="checkbox" name="get_spam" required>',
        )

        # 'True' or 'true' should be rendered without a value attribute
        f = SignupForm({"email": "test@example.com", "get_spam": "True"}, auto_id=False)
        self.assertHTMLEqual(
            str(f["get_spam"]),
            '<input checked type="checkbox" name="get_spam" required>',
        )

        f = SignupForm({"email": "test@example.com", "get_spam": "true"}, auto_id=False)
        self.assertHTMLEqual(
            str(f["get_spam"]),
            '<input checked type="checkbox" name="get_spam" required>',
        )

        # A value of 'False' or 'false' should be rendered unchecked
        f = SignupForm(
            {"email": "test@example.com", "get_spam": "False"}, auto_id=False
        )
        self.assertHTMLEqual(
            str(f["get_spam"]),
            '<input type="checkbox" name="get_spam" aria-invalid="true" required>',
        )

        f = SignupForm(
            {"email": "test@example.com", "get_spam": "false"}, auto_id=False
        )
        self.assertHTMLEqual(
            str(f["get_spam"]),
            '<input type="checkbox" name="get_spam" aria-invalid="true" required>',
        )

        # A value of '0' should be interpreted as a True value (#16820)
        f = SignupForm({"email": "test@example.com", "get_spam": "0"})
        self.assertTrue(f.is_valid())
        self.assertTrue(f.cleaned_data.get("get_spam"))