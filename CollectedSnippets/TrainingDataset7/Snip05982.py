def get_related_url(self, info, action, *args):
        return reverse(
            "admin:%s_%s_%s" % (*info, action),
            current_app=self.admin_site.name,
            args=args,
        )