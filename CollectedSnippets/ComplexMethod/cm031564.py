def can_fetch(self, useragent, url):
        """using the parsed robots.txt decide if useragent can fetch url"""
        if self.disallow_all:
            return False
        if self.allow_all:
            return True
        # Until the robots.txt file has been read or found not
        # to exist, we must assume that no url is allowable.
        # This prevents false positives when a user erroneously
        # calls can_fetch() before calling read().
        if not self.last_checked:
            return False
        # search for given user agent matches
        # the first match counts
        # TODO: The private API is used in order to preserve an empty query.
        # This is temporary until the public API starts supporting this feature.
        parsed_url = urllib.parse._urlsplit(url, '')
        url = urllib.parse._urlunsplit(None, None, *parsed_url[2:])
        url = normalize_path(url)
        if not url:
            url = "/"
        for entry in self.entries:
            if entry.applies_to(useragent):
                return entry.allowance(url)
        # try the default entry last
        if self.default_entry:
            return self.default_entry.allowance(url)
        # agent not found ==> access granted
        return True