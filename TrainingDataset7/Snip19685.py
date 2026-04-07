def test_values(self):
        with self.subTest('User.objects.values("pk")'):
            self.assertSequenceEqual(
                User.objects.values("pk").order_by("pk"),
                (
                    {"pk": self.user_1.pk},
                    {"pk": self.user_2.pk},
                    {"pk": self.user_3.pk},
                ),
            )
        with self.subTest('User.objects.values("pk", "email")'):
            self.assertSequenceEqual(
                User.objects.values("pk", "email").order_by("pk"),
                (
                    {"pk": self.user_1.pk, "email": self.USER_1_EMAIL},
                    {"pk": self.user_2.pk, "email": self.USER_2_EMAIL},
                    {"pk": self.user_3.pk, "email": self.USER_3_EMAIL},
                ),
            )
        with self.subTest('User.objects.values("pk", "id")'):
            self.assertSequenceEqual(
                User.objects.values("pk", "id").order_by("pk"),
                (
                    {"pk": self.user_1.pk, "id": self.user_1.id},
                    {"pk": self.user_2.pk, "id": self.user_2.id},
                    {"pk": self.user_3.pk, "id": self.user_3.id},
                ),
            )
        with self.subTest('User.objects.values("pk", "tenant_id", "id")'):
            self.assertSequenceEqual(
                User.objects.values("pk", "tenant_id", "id").order_by("pk"),
                (
                    {
                        "pk": self.user_1.pk,
                        "tenant_id": self.user_1.tenant_id,
                        "id": self.user_1.id,
                    },
                    {
                        "pk": self.user_2.pk,
                        "tenant_id": self.user_2.tenant_id,
                        "id": self.user_2.id,
                    },
                    {
                        "pk": self.user_3.pk,
                        "tenant_id": self.user_3.tenant_id,
                        "id": self.user_3.id,
                    },
                ),
            )
        with self.subTest('User.objects.values("pk", "pk")'):
            self.assertSequenceEqual(
                User.objects.values("pk", "pk").order_by("pk"),
                (
                    {"pk": self.user_1.pk},
                    {"pk": self.user_2.pk},
                    {"pk": self.user_3.pk},
                ),
            )
        with self.subTest('User.objects.values("pk", "id", "pk", "id")'):
            self.assertSequenceEqual(
                User.objects.values("pk", "id", "pk", "id").order_by("pk"),
                (
                    {"pk": self.user_1.pk, "id": self.user_1.id},
                    {"pk": self.user_2.pk, "id": self.user_2.id},
                    {"pk": self.user_3.pk, "id": self.user_3.id},
                ),
            )