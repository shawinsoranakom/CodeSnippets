def test_not_registered(self):
        should_contain = """<li>Secret hideout: underground bunker"""
        response = self.client.get(
            reverse("admin:admin_views_villain_delete", args=(self.v1.pk,))
        )
        self.assertContains(response, should_contain, 1)