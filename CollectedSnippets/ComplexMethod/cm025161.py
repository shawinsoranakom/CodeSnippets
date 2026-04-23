async def async_process_requirements(
        self, name: str, requirements: list[str], is_built_in: bool
    ) -> None:
        """Install the requirements for a component or platform.

        This method is a coroutine. It will raise RequirementsNotFound
        if an requirement can't be satisfied.
        """
        if DEPRECATED_PACKAGES or self.hass.config.skip_pip_packages:
            all_requirements = {
                requirement_string: requirement_details
                for requirement_string in requirements
                if (
                    requirement_details := pkg_util.parse_requirement_safe(
                        requirement_string
                    )
                )
            }
            if DEPRECATED_PACKAGES:
                for requirement_string, requirement_details in all_requirements.items():
                    if deprecation := DEPRECATED_PACKAGES.get(requirement_details.name):
                        reason, breaks_in_ha_version = deprecation
                        _LOGGER.warning(
                            "Detected that %sintegration '%s' %s. %s %s",
                            "" if is_built_in else "custom ",
                            name,
                            f"has requirement '{requirement_string}' which {reason}",
                            (
                                "This will stop working in Home Assistant "
                                f"{breaks_in_ha_version}, please"
                                if breaks_in_ha_version
                                else "Please"
                            ),
                            async_suggest_report_issue(
                                self.hass, integration_domain=name
                            ),
                        )
            if skip_pip_packages := self.hass.config.skip_pip_packages:
                skipped_requirements: set[str] = set()
                for requirement_string, requirement_details in all_requirements.items():
                    if requirement_details.name in skip_pip_packages:
                        _LOGGER.warning(
                            "Skipping requirement %s. This may cause issues",
                            requirement_string,
                        )
                        skipped_requirements.add(requirement_string)
                requirements = [
                    r for r in requirements if r not in skipped_requirements
                ]

        if not (missing := self._find_missing_requirements(requirements)):
            return
        self._raise_for_failed_requirements(name, missing)

        async with self.pip_lock:
            # Recalculate missing again now that we have the lock
            if missing := self._find_missing_requirements(requirements):
                await self._async_process_requirements(name, missing)