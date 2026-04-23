def test_change_view(self):
        # Get the `change_view`.
        response = self.client.get(self.get_change_url())
        self.assertEqual(response.status_code, 200)

        # Check the form action.
        form_action = re.search(
            '<form action="(.*?)" method="post" id="user_form" novalidate>',
            response.text,
        )
        self.assertURLEqual(
            form_action[1], "?%s" % self.get_preserved_filters_querystring()
        )

        # Check the history link.
        history_link = re.search(
            '<a href="(.*?)" class="historylink">History</a>',
            response.text,
        )
        self.assertURLEqual(history_link[1], self.get_history_url())

        # Check the delete link.
        delete_link = re.search(
            '<a role="button" href="(.*?)" class="deletelink">Delete</a>', response.text
        )
        self.assertURLEqual(delete_link[1], self.get_delete_url())

        # Test redirect on "Save".
        post_data = {
            "username": "joepublic",
            "last_login_0": "2007-05-30",
            "last_login_1": "13:20:10",
            "date_joined_0": "2007-05-30",
            "date_joined_1": "13:20:10",
        }

        post_data["_save"] = 1
        response = self.client.post(self.get_change_url(), data=post_data)
        self.assertRedirects(response, self.get_changelist_url())
        post_data.pop("_save")

        # Test redirect on "Save and continue".
        post_data["_continue"] = 1
        response = self.client.post(self.get_change_url(), data=post_data)
        self.assertRedirects(response, self.get_change_url())
        post_data.pop("_continue")

        # Test redirect on "Save and add new".
        post_data["_addanother"] = 1
        response = self.client.post(self.get_change_url(), data=post_data)
        self.assertRedirects(response, self.get_add_url())
        post_data.pop("_addanother")