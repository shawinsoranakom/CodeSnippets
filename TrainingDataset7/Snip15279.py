def remove_url(self, name):
        """
        Remove all entries named 'name' from the ModelAdmin instance URL
        patterns list
        """
        return [url for url in super().get_urls() if url.name != name]