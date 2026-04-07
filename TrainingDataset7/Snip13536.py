def templates(self):
        if self._templates is None:
            self._templates = settings.TEMPLATES

        templates = {}
        backend_names = []
        for tpl in self._templates:
            try:
                # This will raise an exception if 'BACKEND' doesn't exist or
                # isn't a string containing at least one dot.
                default_name = tpl["BACKEND"].rsplit(".", 2)[-2]
            except Exception:
                invalid_backend = tpl.get("BACKEND", "<not defined>")
                raise ImproperlyConfigured(
                    "Invalid BACKEND for a template engine: {}. Check "
                    "your TEMPLATES setting.".format(invalid_backend)
                )

            tpl = {
                "NAME": default_name,
                "DIRS": [],
                "APP_DIRS": False,
                "OPTIONS": {},
                **tpl,
            }

            templates[tpl["NAME"]] = tpl
            backend_names.append(tpl["NAME"])

        counts = Counter(backend_names)
        duplicates = [alias for alias, count in counts.most_common() if count > 1]
        if duplicates:
            raise ImproperlyConfigured(
                "Template engine aliases aren't unique, duplicates: {}. "
                "Set a unique NAME for each engine in settings.TEMPLATES.".format(
                    ", ".join(duplicates)
                )
            )

        return templates