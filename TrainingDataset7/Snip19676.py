def test_update_or_create_user(self):
        test_cases = (
            {
                "pk": self.user_1.pk,
                "defaults": {"email": "user3914@example.com"},
            },
            {
                "pk": (self.tenant_1.id, self.user_1.id),
                "defaults": {"email": "user9375@example.com"},
            },
            {
                "tenant": self.tenant_1,
                "id": self.user_1.id,
                "defaults": {"email": "user3517@example.com"},
            },
            {
                "tenant_id": self.tenant_1.id,
                "id": self.user_1.id,
                "defaults": {"email": "user8391@example.com"},
            },
        )

        for fields in test_cases:
            with self.subTest(fields=fields):
                count = User.objects.count()
                user, created = User.objects.update_or_create(**fields)
                self.assertIs(created, False)
                self.assertEqual(user.id, self.user_1.id)
                self.assertEqual(user.pk, (self.tenant_1.id, self.user_1.id))
                self.assertEqual(user.tenant_id, self.tenant_1.id)
                self.assertEqual(user.email, fields["defaults"]["email"])
                self.assertEqual(count, User.objects.count())