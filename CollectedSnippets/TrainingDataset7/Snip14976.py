def get(self, request, *args, **kwargs):
        locale = get_language()
        domain = kwargs.get("domain", self.domain)
        # If packages are not provided, default to all installed packages, as
        # DjangoTranslation without localedirs harvests them all.
        packages = kwargs.get("packages", "")
        packages = packages.split("+") if packages else self.packages
        paths = self.get_paths(packages) if packages else None
        self.translation = DjangoTranslation(locale, domain=domain, localedirs=paths)
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)