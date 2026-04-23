def filter_credentials(
        credentials: dict[str, SecretStr] | None,
        provider: Provider,
        require_credentials: bool,
    ) -> dict[str, str]:
        """Filter credentials and check if they match provider requirements."""
        filtered_credentials = {}

        if provider.credentials:
            if credentials is None:
                credentials = {}

            for c in provider.credentials:
                v = credentials.get(c)
                secret = v.get_secret_value() if v else None
                if c not in credentials or not secret:
                    if require_credentials:
                        website = provider.website or ""
                        extra_msg = f" Check {website} to get it." if website else ""
                        raise OpenBBError(
                            f"Missing credential '{c}'.{extra_msg} Refer to the documentation for setting provider "
                            "credentials at https://docs.openbb.co/platform/settings/user_settings/api_keys."
                        )
                else:
                    filtered_credentials[c] = secret

        return filtered_credentials