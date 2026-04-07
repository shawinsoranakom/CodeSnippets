def test_bug_17944_empty_password(self):
        user = User.objects.get(username="empty_password")
        form = UserChangeForm(instance=user)
        self.assertIn(_("No password set."), form.as_table())