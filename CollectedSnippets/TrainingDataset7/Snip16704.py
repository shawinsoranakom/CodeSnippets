def test_change_view_close_link(self):
        viewuser = User.objects.create_user(
            username="view", password="secret", is_staff=True
        )
        viewuser.user_permissions.add(
            get_perm(User, get_permission_codename("view", User._meta))
        )
        self.client.force_login(viewuser)
        response = self.client.get(self.get_change_url())
        close_link = re.search(
            '<a role="button" href="(.*?)" class="closelink">Close</a>', response.text
        )
        close_link = close_link[1].replace("&amp;", "&")
        self.assertURLEqual(close_link, self.get_changelist_url())