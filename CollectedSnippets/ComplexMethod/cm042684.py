def _link_allowed(self, link: Link) -> bool:
        if not _is_valid_url(link.url):
            return False
        if self.allow_res and not _matches(link.url, self.allow_res):
            return False
        if self.deny_res and _matches(link.url, self.deny_res):
            return False
        parsed_url = urlparse(link.url)
        if self.allow_domains and not url_is_from_any_domain(
            parsed_url, self.allow_domains
        ):
            return False
        if self.deny_domains and url_is_from_any_domain(parsed_url, self.deny_domains):
            return False
        if self.deny_extensions and url_has_any_extension(
            parsed_url, self.deny_extensions
        ):
            return False
        return not self.restrict_text or _matches(link.text, self.restrict_text)