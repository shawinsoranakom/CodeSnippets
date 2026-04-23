def test_basic(self):
        active_users = [self.user1, self.user2]
        tests = [
            ({}, [*active_users, self.superuser]),
            ({"obj": self.user1}, []),
            # Only inactive users.
            ({"is_active": False}, [self.inactive_user]),
            # All users.
            ({"is_active": None}, [*active_users, self.superuser, self.inactive_user]),
            # Exclude superusers.
            ({"include_superusers": False}, active_users),
            (
                {"include_superusers": False, "is_active": False},
                [self.inactive_user],
            ),
            (
                {"include_superusers": False, "is_active": None},
                [*active_users, self.inactive_user],
            ),
        ]
        for kwargs, expected_users in tests:
            for perm in ("auth.test", self.permission):
                with self.subTest(perm=perm, **kwargs):
                    self.assertCountEqual(
                        User.objects.with_perm(perm, **kwargs),
                        expected_users,
                    )