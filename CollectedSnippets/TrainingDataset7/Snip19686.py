def test_foreign_object_values(self):
        Comment.objects.create(id=1, user=self.user_1, integer=42)
        testcases = {
            "all": Comment.objects.all(),
            "exclude_user_email": Comment.objects.exclude(user__email__endswith="net"),
        }
        for name, queryset in testcases.items():
            with self.subTest(name=name):
                values = list(queryset.values("user", "integer"))
                self.assertEqual(
                    values[0]["user"], (self.user_1.tenant_id, self.user_1.id)
                )
                self.assertEqual(values[0]["integer"], 42)