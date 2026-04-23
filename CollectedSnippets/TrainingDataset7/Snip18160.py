def test_nonexistent_permission(self):
        self.assertSequenceEqual(User.objects.with_perm("auth.perm"), [self.superuser])