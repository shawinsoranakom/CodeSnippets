async def _async_update_data(self) -> dict[str, IntegrationAlert]:
        response = await async_get_clientsession(self.hass).get(
            "https://alerts.home-assistant.io/alerts.json",
            timeout=REQUEST_TIMEOUT,
        )
        alerts = await response.json()

        result = {}

        for alert in alerts:
            if "integrations" not in alert:
                continue

            if "homeassistant" in alert:
                if "affected_from_version" in alert["homeassistant"]:
                    affected_from_version = AwesomeVersion(
                        alert["homeassistant"]["affected_from_version"],
                    )
                    if self.ha_version < affected_from_version:
                        continue
                if "resolved_in_version" in alert["homeassistant"]:
                    resolved_in_version = AwesomeVersion(
                        alert["homeassistant"]["resolved_in_version"],
                    )
                    if self.ha_version >= resolved_in_version:
                        continue

            if self.supervisor and "supervisor" in alert:
                if (supervisor_info := get_supervisor_info(self.hass)) is None:
                    continue

                if "affected_from_version" in alert["supervisor"]:
                    affected_from_version = AwesomeVersion(
                        alert["supervisor"]["affected_from_version"],
                    )
                    if supervisor_info["version"] < affected_from_version:
                        continue
                if "resolved_in_version" in alert["supervisor"]:
                    resolved_in_version = AwesomeVersion(
                        alert["supervisor"]["resolved_in_version"],
                    )
                    if supervisor_info["version"] >= resolved_in_version:
                        continue

            for integration in alert["integrations"]:
                if "package" not in integration:
                    continue

                if integration["package"] not in self.hass.config.components:
                    continue

                integration_alert = IntegrationAlert(
                    alert_id=alert["id"],
                    integration=integration["package"],
                    filename=alert["filename"],
                    date_updated=alert.get("updated"),
                )

                result[integration_alert.issue_id] = integration_alert

        return result