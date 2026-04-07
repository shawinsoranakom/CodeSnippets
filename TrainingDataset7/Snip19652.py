def test_fields(self):
        # tenant_1
        self.assertSequenceEqual(
            self.tenant_1.user_set.order_by("pk"),
            [self.user_1, self.user_2],
        )
        self.assertSequenceEqual(
            self.tenant_1.comments.order_by("pk"),
            [self.comment_1, self.comment_2, self.comment_3],
        )

        # tenant_2
        self.assertSequenceEqual(self.tenant_2.user_set.order_by("pk"), [self.user_3])
        self.assertSequenceEqual(
            self.tenant_2.comments.order_by("pk"), [self.comment_4]
        )

        # user_1
        self.assertEqual(self.user_1.id, 1)
        self.assertEqual(self.user_1.tenant_id, self.tenant_1.id)
        self.assertEqual(self.user_1.tenant, self.tenant_1)
        self.assertEqual(self.user_1.pk, (self.tenant_1.id, self.user_1.id))
        self.assertSequenceEqual(
            self.user_1.comments.order_by("pk"), [self.comment_1, self.comment_2]
        )

        # user_2
        self.assertEqual(self.user_2.id, 2)
        self.assertEqual(self.user_2.tenant_id, self.tenant_1.id)
        self.assertEqual(self.user_2.tenant, self.tenant_1)
        self.assertEqual(self.user_2.pk, (self.tenant_1.id, self.user_2.id))
        self.assertSequenceEqual(self.user_2.comments.order_by("pk"), [self.comment_3])

        # comment_1
        self.assertEqual(self.comment_1.id, 1)
        self.assertEqual(self.comment_1.user_id, self.user_1.id)
        self.assertEqual(self.comment_1.user, self.user_1)
        self.assertEqual(self.comment_1.tenant_id, self.tenant_1.id)
        self.assertEqual(self.comment_1.tenant, self.tenant_1)
        self.assertEqual(self.comment_1.pk, (self.tenant_1.id, self.user_1.id))