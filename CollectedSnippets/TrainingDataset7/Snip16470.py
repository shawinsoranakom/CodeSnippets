def test_recentactions_description(self):
        response = self.client.get(reverse("admin:index"))
        for operation in ["Added", "Changed", "Deleted"]:
            with self.subTest(operation):
                self.assertContains(
                    response, f'<span class="visually-hidden">{operation}:'
                )