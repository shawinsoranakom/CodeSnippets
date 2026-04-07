def test_save_button(self):
        group_count = Group.objects.count()
        response = self.client.post(
            reverse("admin:auth_group_add"),
            {
                "name": "newgroup",
            },
        )

        Group.objects.order_by("-id")[0]
        self.assertRedirects(response, reverse("admin:auth_group_changelist"))
        self.assertEqual(Group.objects.count(), group_count + 1)