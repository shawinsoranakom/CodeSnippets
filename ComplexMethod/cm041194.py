def _is_in_allowed_origins(allowed_origins: list[str], origin: str) -> bool:
        """Returns true if the `origin` is in the `allowed_origins`."""
        for allowed_origin in allowed_origins:
            if allowed_origin == "*" or origin == allowed_origin:
                return True

        # performance wise, this is not very heavy because most of the regular requests will match above
        # this would be executed mostly when rejecting or actually using content served by CloudFront or S3 website
        for dynamic_origin in DYNAMIC_INTERNAL_ORIGINS:
            match = dynamic_origin.match(origin)
            if (
                match
                and (match.group(2) in _ALLOWED_INTERNAL_DOMAINS)
                and (not (port := match.group(3)) or int(port[1:]) in _ALLOWED_INTERNAL_PORTS)
            ):
                return True

        return False