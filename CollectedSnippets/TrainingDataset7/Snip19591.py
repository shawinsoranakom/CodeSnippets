def test_update_or_create_user(self):
        test_cases = (
            {
                "pk": (self.tenant.id, 2931),
                "defaults": {"email": "user2931@example.com"},
            },
            {
                "tenant": self.tenant,
                "id": 6428,
                "defaults": {"email": "user6428@example.com"},
            },
            {
                "tenant_id": self.tenant.id,
                "id": 5278,
                "defaults": {"email": "user5278@example.com"},
            },
        )

        for fields in test_cases:
            with self.subTest(fields=fields):
                count = User.objects.count()
                user, created = User.objects.update_or_create(**fields)
                self.assertIs(created, True)
                self.assertIsNotNone(user.id)
                self.assertEqual(user.pk, (self.tenant.id, user.id))
                self.assertEqual(user.tenant_id, self.tenant.id)
                self.assertEqual(user.email, fields["defaults"]["email"])
                self.assertEqual(user.email, f"user{user.id}@example.com")
                self.assertEqual(count + 1, User.objects.count())