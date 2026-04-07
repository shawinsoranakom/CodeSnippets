def test_change_view_history_link(self):
        """
        Object history button link should work and contain the pk value quoted.
        """
        url = reverse(
            "admin:%s_modelwithstringprimarykey_change"
            % ModelWithStringPrimaryKey._meta.app_label,
            args=(quote(self.pk),),
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        expected_link = reverse(
            "admin:%s_modelwithstringprimarykey_history"
            % ModelWithStringPrimaryKey._meta.app_label,
            args=(quote(self.pk),),
        )
        self.assertContains(
            response,
            '<a href="%s" class="historylink"' % escape(expected_link),
        )