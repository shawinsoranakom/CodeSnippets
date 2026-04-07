def render(self, context):
        if "request" in context:
            site_pk = get_current_site(context["request"]).pk
        else:
            site_pk = settings.SITE_ID
        flatpages = FlatPage.objects.filter(sites__id=site_pk)
        # If a prefix was specified, add a filter
        if self.starts_with:
            flatpages = flatpages.filter(
                url__startswith=self.starts_with.resolve(context)
            )

        # If the provided user is not authenticated, or no user
        # was provided, filter the list to only public flatpages.
        if self.user:
            user = self.user.resolve(context)
            if not user.is_authenticated:
                flatpages = flatpages.filter(registration_required=False)
        else:
            flatpages = flatpages.filter(registration_required=False)

        context[self.context_name] = flatpages
        return ""