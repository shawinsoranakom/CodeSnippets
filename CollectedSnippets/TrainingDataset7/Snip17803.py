def test_bug_19349_bound_password_field(self):
        user = User.objects.get(username="testclient")
        form = UserChangeForm(data={}, instance=user)
        # When rendering the bound password field,
        # ReadOnlyPasswordHashWidget needs the initial
        # value to render correctly
        self.assertEqual(form.initial["password"], form["password"].value())