def load(self) -> BaseModel:
        """Load credentials from providers."""
        self.from_providers()
        self.from_obbject()
        path = Path(USER_SETTINGS_PATH)
        additional: dict = {}

        if path.exists():
            with open(USER_SETTINGS_PATH, encoding="utf-8") as f:
                data = json.load(f)
                if "credentials" in data:
                    additional = data["credentials"]

        additional = self._normalize_credential_map(additional)

        all_keys = [
            key
            for keys in ProviderInterface().credentials.values()
            if keys
            for key in keys
        ]

        env_credentials: dict[str, SecretStr] = {}
        for env_key, value in os.environ.items():
            if not value:
                continue
            lower_key = env_key.lower()
            if lower_key in all_keys or env_key.endswith("API_KEY"):
                canonical_key = lower_key if lower_key in all_keys else lower_key
                env_credentials[canonical_key] = SecretStr(value)

        if env_credentials:
            additional.update(env_credentials)

        additional = self._normalize_credential_map(additional)

        env_overrides = {
            key: additional[key]
            for key in env_credentials
            if key in additional and additional[key] not in (None, "")
        }

        model = create_model(
            "Credentials",
            __config__=ConfigDict(validate_assignment=True, populate_by_name=True),
            **self.format_credentials(additional),  # type: ignore
        )
        model._env_defaults = env_overrides  # type: ignore # pylint: disable=W0212
        model.origins = self.credentials

        return model