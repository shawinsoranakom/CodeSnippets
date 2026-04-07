def _response_post_save(self, request, obj):
        if self.has_view_or_change_permission(request):
            post_url = reverse(
                "admin:%s_%s_changelist" % (self.opts.app_label, self.opts.model_name),
                current_app=self.admin_site.name,
            )
            preserved_filters = self.get_preserved_filters(request)
            post_url = add_preserved_filters(
                {"preserved_filters": preserved_filters, "opts": self.opts}, post_url
            )
        else:
            post_url = reverse("admin:index", current_app=self.admin_site.name)
        return HttpResponseRedirect(post_url)