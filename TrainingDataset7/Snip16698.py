def get_add_url(self, add_preserved_filters=True):
        url = reverse("admin:auth_user_add", current_app=self.admin_site.name)
        if add_preserved_filters:
            url = "%s?%s" % (url, self.get_preserved_filters_querystring())
        return url