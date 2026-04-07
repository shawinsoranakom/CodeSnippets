def get_urls(self):
        # Opt-out of append slash for single model.
        urls = super().get_urls()
        for pattern in urls:
            pattern.callback = no_append_slash(pattern.callback)
        return urls