def cache_key(self, template_name, skip=None):
        """
        Generate a cache key for the template name and skip.

        If skip is provided, only origins that match template_name are included
        in the cache key. This ensures each template is only parsed and cached
        once if contained in different extend chains like:

            x -> a -> a
            y -> a -> a
            z -> a -> a
        """
        skip_prefix = ""

        if skip:
            matching = [
                origin.name for origin in skip if origin.template_name == template_name
            ]
            if matching:
                skip_prefix = self.generate_hash(matching)

        return "-".join(s for s in (str(template_name), skip_prefix) if s)