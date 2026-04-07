def test_basic_edit_GET(self):
        """
        A smoke test to ensure GET on the change_view works.
        """
        response = self.client.get(
            reverse(
                "admin:generic_inline_admin_episode_change", args=(self.episode_pk,)
            )
        )
        self.assertEqual(response.status_code, 200)