def get_absolute_url(self):
        from .views import flatpage

        for url in (self.url.lstrip("/"), self.url):
            try:
                return reverse(flatpage, kwargs={"url": url})
            except NoReverseMatch:
                pass
        # Handle script prefix manually because we bypass reverse()
        return iri_to_uri(get_script_prefix().rstrip("/") + self.url)