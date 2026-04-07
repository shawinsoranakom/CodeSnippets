def test_get_or_create_user(self):
        test_cases = (
            {
                "pk": (self.tenant.id, 8314),
                "defaults": {"email": "user8314@example.com"},
            },
            {
                "tenant": self.tenant,
                "id": 3142,
                "defaults": {"email": "user3142@example.com"},
            },
            {
                "tenant_id": self.tenant.id,
                "id": 4218,
                "defaults": {"email": "user4218@example.com"},
            },
        )

        for fields in test_cases:
            with self.subTest(fields=fields):
                count = User.objects.count()
                user, created = User.objects.get_or_create(**fields)
                self.assertIs(created, True)
                self.assertIsNotNone(user.id)
                self.assertEqual(user.pk, (self.tenant.id, user.id))
                self.assertEqual(user.tenant_id, self.tenant.id)
                self.assertEqual(user.email, fields["defaults"]["email"])
                self.assertEqual(user.email, f"user{user.id}@example.com")
                self.assertEqual(count + 1, User.objects.count())