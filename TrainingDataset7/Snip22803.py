def test_boundfield_values(self):
        # It's possible to get to the value which would be used for rendering
        # the widget for a field by using the BoundField's value method.

        class UserRegistration(Form):
            username = CharField(max_length=10, initial="djangonaut")
            password = CharField(widget=PasswordInput)

        unbound = UserRegistration()
        bound = UserRegistration({"password": "foo"})
        self.assertIsNone(bound["username"].value())
        self.assertEqual(unbound["username"].value(), "djangonaut")
        self.assertEqual(bound["password"].value(), "foo")
        self.assertIsNone(unbound["password"].value())