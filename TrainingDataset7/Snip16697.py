def get_changelist_url(self):
        return "%s?%s" % (
            reverse("admin:auth_user_changelist", current_app=self.admin_site.name),
            self.get_changelist_filters_querystring(),
        )