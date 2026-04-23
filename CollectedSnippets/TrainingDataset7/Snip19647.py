def test_get_or_create_user(self):
        test_cases = (
            {
                "pk": self.user_1.pk,
                "defaults": {"email": "user9201@example.com"},
            },
            {
                "pk": (self.tenant_1.id, self.user_1.id),
                "defaults": {"email": "user9201@example.com"},
            },
            {
                "tenant": self.tenant_1,
                "id": self.user_1.id,
                "defaults": {"email": "user3512@example.com"},
            },
            {
                "tenant_id": self.tenant_1.id,
                "id": self.user_1.id,
                "defaults": {"email": "user8239@example.com"},
            },
        )

        for fields in test_cases:
            with self.subTest(fields=fields):
                count = User.objects.count()
                user, created = User.objects.get_or_create(**fields)
                self.assertIs(created, False)
                self.assertEqual(user.id, self.user_1.id)
                self.assertEqual(user.pk, (self.tenant_1.id, self.user_1.id))
                self.assertEqual(user.tenant_id, self.tenant_1.id)
                self.assertEqual(user.email, self.user_1.email)
                self.assertEqual(count, User.objects.count())