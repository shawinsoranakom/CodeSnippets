def test_save_user(self):
        test_cases = (
            {"tenant": self.tenant, "id": 9241, "email": "user9241@example.com"},
            {"tenant_id": self.tenant.id, "id": 5132, "email": "user5132@example.com"},
            {"pk": (self.tenant.id, 3014), "email": "user3014@example.com"},
        )

        for fields in test_cases:
            with self.subTest(fields=fields):
                count = User.objects.count()
                user = User(**fields)
                self.assertIsNotNone(user.id)
                self.assertIsNotNone(user.email)
                user.save()
                self.assertEqual(user.tenant_id, self.tenant.id)
                self.assertEqual(user.tenant, self.tenant)
                self.assertIsNotNone(user.id)
                self.assertEqual(user.pk, (self.tenant.id, user.id))
                self.assertEqual(user.email, fields["email"])
                self.assertEqual(user.email, f"user{user.id}@example.com")
                self.assertEqual(count + 1, User.objects.count())