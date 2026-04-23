def get_history_url(self, user_id=None):
        if user_id is None:
            user_id = self.get_sample_user_id()
        return "%s?%s" % (
            reverse(
                "admin:auth_user_history",
                args=(user_id,),
                current_app=self.admin_site.name,
            ),
            self.get_preserved_filters_querystring(),
        )