def _compile(self, regex):
        try:
            return re.compile(regex)
        except re.error as e:
            raise ImproperlyConfigured(
                f'"{regex}" is not a valid regular expression: {e}'
            ) from e