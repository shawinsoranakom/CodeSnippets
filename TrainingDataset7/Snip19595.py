def test_delete_tenant_by_pk(self):
        result = Tenant.objects.filter(pk=self.tenant_1.pk).delete()

        self.assertEqual(
            result,
            (
                3,
                {
                    "composite_pk.Comment": 1,
                    "composite_pk.User": 1,
                    "composite_pk.Tenant": 1,
                },
            ),
        )

        self.assertIs(Tenant.objects.filter(pk=self.tenant_1.pk).exists(), False)
        self.assertIs(Tenant.objects.filter(pk=self.tenant_2.pk).exists(), True)
        self.assertIs(User.objects.filter(pk=self.user_1.pk).exists(), False)
        self.assertIs(User.objects.filter(pk=self.user_2.pk).exists(), True)
        self.assertIs(Comment.objects.filter(pk=self.comment_1.pk).exists(), False)
        self.assertIs(Comment.objects.filter(pk=self.comment_2.pk).exists(), True)
        self.assertIs(Comment.objects.filter(pk=self.comment_3.pk).exists(), True)