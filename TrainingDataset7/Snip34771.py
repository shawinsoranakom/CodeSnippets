def test_redirect_to_self_with_changing_query(self):
        "Redirections don't loop forever even if query is changing"
        with self.assertRaises(RedirectCycleError):
            self.client.get(
                "/redirect_to_self_with_changing_query_view/",
                {"counter": "0"},
                follow=True,
            )