def test_get_user(self):
        test_cases = (
            {"pk": self.user_1.pk},
            {"pk": (self.tenant_1.id, self.user_1.id)},
            {"id": self.user_1.id},
        )

        for lookup in test_cases:
            with self.subTest(lookup=lookup):
                self.assertEqual(User.objects.get(**lookup), self.user_1)