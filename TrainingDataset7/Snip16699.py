def get_change_url(self, user_id=None, add_preserved_filters=True):
        if user_id is None:
            user_id = self.get_sample_user_id()
        url = reverse(
            "admin:auth_user_change", args=(user_id,), current_app=self.admin_site.name
        )
        if add_preserved_filters:
            url = "%s?%s" % (url, self.get_preserved_filters_querystring())
        return url