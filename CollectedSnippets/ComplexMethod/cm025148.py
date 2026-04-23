def resolve_from_root(
        cls, hass: HomeAssistant, root_module: ModuleType, domain: str
    ) -> Integration | None:
        """Resolve an integration from a root module."""
        for base in root_module.__path__:
            manifest_path = pathlib.Path(base) / domain / "manifest.json"

            if not manifest_path.is_file():
                continue

            try:
                manifest = cast(Manifest, json_loads(manifest_path.read_text()))
            except JSON_DECODE_EXCEPTIONS as err:
                _LOGGER.error(
                    "Error parsing manifest.json file at %s: %s", manifest_path, err
                )
                continue

            file_path = manifest_path.parent
            # Avoid the listdir for virtual integrations
            # as they cannot have any platforms
            is_virtual = manifest.get("integration_type") == "virtual"
            integration = cls(
                hass,
                f"{root_module.__name__}.{domain}",
                file_path,
                manifest,
                None if is_virtual else set(os.listdir(file_path)),
            )

            if not integration.import_executor:
                _LOGGER.warning(IMPORT_EVENT_LOOP_WARNING, integration.domain)

            if integration.is_built_in:
                return integration

            _LOGGER.warning(CUSTOM_WARNING, integration.domain)

            if integration.version is None:
                _LOGGER.error(
                    (
                        "The custom integration '%s' does not have a version key in the"
                        " manifest file and was blocked from loading. See"
                        " https://developers.home-assistant.io"
                        "/blog/2021/01/29/custom-integration-changes#versions"
                        " for more details"
                    ),
                    integration.domain,
                )
                return None
            try:
                AwesomeVersion(
                    integration.version,
                    ensure_strategy=[
                        AwesomeVersionStrategy.CALVER,
                        AwesomeVersionStrategy.SEMVER,
                        AwesomeVersionStrategy.SIMPLEVER,
                        AwesomeVersionStrategy.BUILDVER,
                        AwesomeVersionStrategy.PEP440,
                    ],
                )
            except AwesomeVersionException:
                _LOGGER.error(
                    (
                        "The custom integration '%s' does not have a valid version key"
                        " (%s) in the manifest file and was blocked from loading. See"
                        " https://developers.home-assistant.io"
                        "/blog/2021/01/29/custom-integration-changes#versions"
                        " for more details"
                    ),
                    integration.domain,
                    integration.version,
                )
                return None

            if blocked := BLOCKED_CUSTOM_INTEGRATIONS.get(integration.domain):
                if _version_blocked(integration.version, blocked):
                    _LOGGER.error(
                        (
                            "Version %s of custom integration '%s' %s and was blocked "
                            "from loading, please %s"
                        ),
                        integration.version,
                        integration.domain,
                        blocked.reason,
                        async_suggest_report_issue(None, integration=integration),
                    )
                    return None

            return integration

        return None