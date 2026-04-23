def get_urls(self):
        urlpatterns = super().get_urls()
        urlpatterns.append(
            path(
                "extra.json",
                self.admin_site.admin_view(self.extra_json),
                name="article_extra_json",
            )
        )
        return urlpatterns