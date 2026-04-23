def test_values_list(self):
        with self.subTest('User.objects.values_list("pk")'):
            self.assertSequenceEqual(
                User.objects.values_list("pk").order_by("pk"),
                (
                    (self.user_1.pk,),
                    (self.user_2.pk,),
                    (self.user_3.pk,),
                ),
            )
        with self.subTest('User.objects.values_list("pk", "email")'):
            self.assertSequenceEqual(
                User.objects.values_list("pk", "email").order_by("pk"),
                (
                    (self.user_1.pk, self.USER_1_EMAIL),
                    (self.user_2.pk, self.USER_2_EMAIL),
                    (self.user_3.pk, self.USER_3_EMAIL),
                ),
            )
        with self.subTest('User.objects.values_list("pk", "id")'):
            self.assertSequenceEqual(
                User.objects.values_list("pk", "id").order_by("pk"),
                (
                    (self.user_1.pk, self.user_1.id),
                    (self.user_2.pk, self.user_2.id),
                    (self.user_3.pk, self.user_3.id),
                ),
            )
        with self.subTest('User.objects.values_list("pk", "tenant_id", "id")'):
            self.assertSequenceEqual(
                User.objects.values_list("pk", "tenant_id", "id").order_by("pk"),
                (
                    (self.user_1.pk, self.user_1.tenant_id, self.user_1.id),
                    (self.user_2.pk, self.user_2.tenant_id, self.user_2.id),
                    (self.user_3.pk, self.user_3.tenant_id, self.user_3.id),
                ),
            )
        with self.subTest('User.objects.values_list("pk", flat=True)'):
            self.assertSequenceEqual(
                User.objects.values_list("pk", flat=True).order_by("pk"),
                (
                    self.user_1.pk,
                    self.user_2.pk,
                    self.user_3.pk,
                ),
            )
        with self.subTest('Post.objects.values_list("pk", flat=True)'):
            self.assertSequenceEqual(
                Post.objects.values_list("pk", flat=True).order_by("pk"),
                (
                    (self.tenant_1.id, UUID(self.POST_1_ID)),
                    (self.tenant_1.id, UUID(self.POST_2_ID)),
                    (self.tenant_2.id, UUID(self.POST_3_ID)),
                ),
            )
        with self.subTest('Post.objects.values_list("pk")'):
            self.assertSequenceEqual(
                Post.objects.values_list("pk").order_by("pk"),
                (
                    ((self.tenant_1.id, UUID(self.POST_1_ID)),),
                    ((self.tenant_1.id, UUID(self.POST_2_ID)),),
                    ((self.tenant_2.id, UUID(self.POST_3_ID)),),
                ),
            )
        with self.subTest('Post.objects.values_list("pk", "id")'):
            self.assertSequenceEqual(
                Post.objects.values_list("pk", "id").order_by("pk"),
                (
                    ((self.tenant_1.id, UUID(self.POST_1_ID)), UUID(self.POST_1_ID)),
                    ((self.tenant_1.id, UUID(self.POST_2_ID)), UUID(self.POST_2_ID)),
                    ((self.tenant_2.id, UUID(self.POST_3_ID)), UUID(self.POST_3_ID)),
                ),
            )
        with self.subTest('Post.objects.values_list("id", "pk")'):
            self.assertSequenceEqual(
                Post.objects.values_list("id", "pk").order_by("pk"),
                (
                    (UUID(self.POST_1_ID), (self.tenant_1.id, UUID(self.POST_1_ID))),
                    (UUID(self.POST_2_ID), (self.tenant_1.id, UUID(self.POST_2_ID))),
                    (UUID(self.POST_3_ID), (self.tenant_2.id, UUID(self.POST_3_ID))),
                ),
            )
        with self.subTest('User.objects.values_list("pk", named=True)'):
            Row = namedtuple("Row", ["pk"])
            self.assertSequenceEqual(
                User.objects.values_list("pk", named=True).order_by("pk"),
                (
                    Row(pk=self.user_1.pk),
                    Row(pk=self.user_2.pk),
                    Row(pk=self.user_3.pk),
                ),
            )
        with self.subTest('User.objects.values_list("pk", "pk")'):
            self.assertSequenceEqual(
                User.objects.values_list("pk", "pk").order_by("pk"),
                (
                    (self.user_1.pk, self.user_1.pk),
                    (self.user_2.pk, self.user_2.pk),
                    (self.user_3.pk, self.user_3.pk),
                ),
            )
        with self.subTest('User.objects.values_list("pk", "id", "pk", "id")'):
            self.assertSequenceEqual(
                User.objects.values_list("pk", "id", "pk", "id").order_by("pk"),
                (
                    (self.user_1.pk, self.user_1.id, self.user_1.pk, self.user_1.id),
                    (self.user_2.pk, self.user_2.id, self.user_2.pk, self.user_2.id),
                    (self.user_3.pk, self.user_3.id, self.user_3.pk, self.user_3.id),
                ),
            )