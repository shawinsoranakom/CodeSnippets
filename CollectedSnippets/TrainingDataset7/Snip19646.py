def test_get_comment(self):
        test_cases = (
            {"pk": self.comment_1.pk},
            {"pk": (self.tenant_1.id, self.comment_1.id)},
            {"id": self.comment_1.id},
            {"user": self.user_1},
            {"user_id": self.user_1.id},
            {"user__id": self.user_1.id},
            {"user__pk": self.user_1.pk},
            {"tenant": self.tenant_1},
            {"tenant_id": self.tenant_1.id},
            {"tenant__id": self.tenant_1.id},
            {"tenant__pk": self.tenant_1.pk},
        )

        for lookup in test_cases:
            with self.subTest(lookup=lookup):
                self.assertEqual(Comment.objects.get(**lookup), self.comment_1)