def test_unusable_password(self):
        user = User.objects.get(username="unusable_password")
        form = UserChangeForm(instance=user)
        self.assertIn(_("No password set."), form.as_table())