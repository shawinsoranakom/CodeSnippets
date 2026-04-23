def charset(self):
        if self._charset is not None:
            return self._charset
        # The Content-Type header may not yet be set, because the charset is
        # being inserted *into* it.
        if content_type := self.headers.get("Content-Type"):
            if matched := _charset_from_content_type_re.search(content_type):
                # Extract the charset and strip its double quotes.
                # Note that having parsed it from the Content-Type, we don't
                # store it back into the _charset for later intentionally, to
                # allow for the Content-Type to be switched again later.
                return matched["charset"].replace('"', "")
        return settings.DEFAULT_CHARSET