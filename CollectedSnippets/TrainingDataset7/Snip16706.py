def test_add_view(self):
        # Get the `add_view`.
        response = self.client.get(self.get_add_url())
        self.assertEqual(response.status_code, 200)

        # Check the form action.
        form_action = re.search(
            '<form action="(.*?)" method="post" id="user_form" novalidate>',
            response.text,
        )
        self.assertURLEqual(
            form_action[1], "?%s" % self.get_preserved_filters_querystring()
        )

        post_data = {
            "username": "dummy",
            "password1": "test",
            "password2": "test",
        }

        # Test redirect on "Save".
        post_data["_save"] = 1
        response = self.client.post(self.get_add_url(), data=post_data)
        self.assertRedirects(
            response, self.get_change_url(User.objects.get(username="dummy").pk)
        )
        post_data.pop("_save")

        # Test redirect on "Save and continue".
        post_data["username"] = "dummy2"
        post_data["_continue"] = 1
        response = self.client.post(self.get_add_url(), data=post_data)
        self.assertRedirects(
            response, self.get_change_url(User.objects.get(username="dummy2").pk)
        )
        post_data.pop("_continue")

        # Test redirect on "Save and add new".
        post_data["username"] = "dummy3"
        post_data["_addanother"] = 1
        response = self.client.post(self.get_add_url(), data=post_data)
        self.assertRedirects(response, self.get_add_url())
        post_data.pop("_addanother")