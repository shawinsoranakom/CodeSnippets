def test_changelist_view(self):
        response = self.client.get(self.get_changelist_url())
        self.assertEqual(response.status_code, 200)

        # Check the `change_view` link has the correct querystring.
        detail_link = re.search(
            '<a href="(.*?)">{}</a>'.format(self.joepublicuser.username),
            response.text,
        )
        self.assertURLEqual(detail_link[1], self.get_change_url())