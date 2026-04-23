def test_proxy_model_content_type_is_used_for_log_entries(self):
        """
        Log entries for proxy models should have the proxy model's contenttype
        (#21084).
        """
        proxy_content_type = ContentType.objects.get_for_model(
            ArticleProxy, for_concrete_model=False
        )
        post_data = {
            "site": self.site.pk,
            "title": "Foo",
            "hist": "Bar",
            "created_0": "2015-12-25",
            "created_1": "00:00",
        }
        changelist_url = reverse("admin:admin_utils_articleproxy_changelist")
        expected_signals = []
        self.assertEqual(self.signals, expected_signals)

        # add
        proxy_add_url = reverse("admin:admin_utils_articleproxy_add")
        response = self.client.post(proxy_add_url, post_data)
        self.assertRedirects(response, changelist_url)
        proxy_addition_log = LogEntry.objects.latest("id")
        self.assertEqual(proxy_addition_log.action_flag, ADDITION)
        self.assertEqual(proxy_addition_log.content_type, proxy_content_type)
        expected_signals.extend(
            [("pre_save", proxy_addition_log), ("post_save", proxy_addition_log, True)]
        )
        self.assertEqual(self.signals, expected_signals)

        # change
        article_id = proxy_addition_log.object_id
        proxy_change_url = reverse(
            "admin:admin_utils_articleproxy_change", args=(article_id,)
        )
        post_data["title"] = "New"
        response = self.client.post(proxy_change_url, post_data)
        self.assertRedirects(response, changelist_url)
        proxy_change_log = LogEntry.objects.latest("id")
        self.assertEqual(proxy_change_log.action_flag, CHANGE)
        self.assertEqual(proxy_change_log.content_type, proxy_content_type)
        expected_signals.extend(
            [("pre_save", proxy_change_log), ("post_save", proxy_change_log, True)]
        )
        self.assertEqual(self.signals, expected_signals)

        # delete
        proxy_delete_url = reverse(
            "admin:admin_utils_articleproxy_delete", args=(article_id,)
        )
        response = self.client.post(proxy_delete_url, {"post": "yes"})
        self.assertRedirects(response, changelist_url)
        proxy_delete_log = LogEntry.objects.latest("id")
        self.assertEqual(proxy_delete_log.action_flag, DELETION)
        self.assertEqual(proxy_delete_log.content_type, proxy_content_type)
        expected_signals.extend(
            [("pre_save", proxy_delete_log), ("post_save", proxy_delete_log, True)]
        )
        self.assertEqual(self.signals, expected_signals)