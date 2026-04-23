def test_create_user(self):
        test_cases = (
            {"tenant": self.tenant, "id": 2412, "email": "user2412@example.com"},
            {"tenant_id": self.tenant.id, "id": 5316, "email": "user5316@example.com"},
            {"pk": (self.tenant.id, 7424), "email": "user7424@example.com"},
        )

        for fields in test_cases:
            with self.subTest(fields=fields):
                count = User.objects.count()
                user = User(**fields)
                obj = User.objects.create(**fields)
                self.assertEqual(obj.tenant_id, self.tenant.id)
                self.assertEqual(obj.id, user.id)
                self.assertEqual(obj.pk, (self.tenant.id, user.id))
                self.assertEqual(obj.email, user.email)
                self.assertEqual(count + 1, User.objects.count())