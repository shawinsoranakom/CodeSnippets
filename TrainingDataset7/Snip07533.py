def get_urls(self, page=1, site=None, protocol=None):
        """
        This method is overridden so the appropriate `geo_format` attribute
        is placed on each URL element.
        """
        urls = Sitemap.get_urls(self, page=page, site=site, protocol=protocol)
        for url in urls:
            url["geo_format"] = self.geo_format
        return urls