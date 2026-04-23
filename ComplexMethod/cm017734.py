def __call__(self, value):
        if not isinstance(value, str) or len(value) > self.max_length:
            raise ValidationError(self.message, code=self.code, params={"value": value})
        if self.unsafe_chars.intersection(value):
            raise ValidationError(self.message, code=self.code, params={"value": value})
        # Check if the scheme is valid.
        scheme = value.split("://")[0].lower()
        if scheme not in self.schemes:
            raise ValidationError(self.message, code=self.code, params={"value": value})

        # Then check full URL
        try:
            splitted_url = urlsplit(value)
        except ValueError:
            raise ValidationError(self.message, code=self.code, params={"value": value})
        super().__call__(value)
        # Now verify IPv6 in the netloc part
        host_match = re.search(r"^\[(.+)\](?::[0-9]{1,5})?$", splitted_url.netloc)
        if host_match:
            potential_ip = host_match[1]
            try:
                validate_ipv6_address(potential_ip)
            except ValidationError:
                raise ValidationError(
                    self.message, code=self.code, params={"value": value}
                )

        # The maximum length of a full host name is 253 characters per RFC 1034
        # section 3.1. It's defined to be 255 bytes or less, but this includes
        # one byte for the length of the name and one byte for the trailing dot
        # that's used to indicate absolute names in DNS.
        if splitted_url.hostname is None or len(splitted_url.hostname) > 253:
            raise ValidationError(self.message, code=self.code, params={"value": value})