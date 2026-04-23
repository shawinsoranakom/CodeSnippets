async def _async_check_deprecation(event: Event) -> None:
        """Check and create deprecation issues after startup."""
        info = await async_get_system_info(hass)

        installation_type = info["installation_type"][15:]
        if installation_type in {"Core", "Container"}:
            deprecated_method = installation_type == "Core"
            bit32 = _is_32_bit()
            arch = info["arch"]
            if bit32 and installation_type == "Container":
                arch = info.get("container_arch", arch)
                ir.async_create_issue(
                    hass,
                    DOMAIN,
                    "deprecated_container",
                    learn_more_url=DEPRECATION_URL,
                    is_fixable=False,
                    severity=IssueSeverity.WARNING,
                    translation_key="deprecated_container",
                    translation_placeholders={"arch": arch},
                )
            deprecated_architecture = bit32 and installation_type != "Container"
            if deprecated_method or deprecated_architecture:
                issue_id = "deprecated"
                if deprecated_method:
                    issue_id += "_method"
                if deprecated_architecture:
                    issue_id += "_architecture"
                ir.async_create_issue(
                    hass,
                    DOMAIN,
                    issue_id,
                    learn_more_url=DEPRECATION_URL,
                    is_fixable=False,
                    severity=IssueSeverity.WARNING,
                    translation_key=issue_id,
                    translation_placeholders={
                        "installation_type": installation_type,
                        "arch": arch,
                    },
                )
        if not info["docker"] and not info["virtualenv"]:
            ir.async_create_issue(
                hass,
                DOMAIN,
                "unsupported_local_deps",
                learn_more_url=DEPRECATION_URL,
                is_fixable=False,
                severity=IssueSeverity.WARNING,
                translation_key="unsupported_local_deps",
            )