async def send_analytics(self, _: datetime | None = None) -> None:
        """Send analytics."""
        if not self.onboarded or not self.preferences.get(ATTR_BASE, False):
            return

        hass = self._hass
        supervisor_info = None
        addons_info: dict[str, Any] | None = None
        operating_system_info: dict[str, Any] = {}

        if self._data.uuid is None:
            self._data.uuid = gen_uuid()
            await self._save()

        if self.supervisor:
            supervisor_info = hassio.get_supervisor_info(hass)
            operating_system_info = hassio.get_os_info(hass) or {}
            addons_info = hassio.get_addons_info(hass) or {}

        system_info = await async_get_system_info(hass)
        integrations = []
        custom_integrations = []
        addons: list[dict[str, Any]] = []
        payload: dict = {
            ATTR_UUID: self.uuid,
            ATTR_VERSION: HA_VERSION,
            ATTR_INSTALLATION_TYPE: system_info[ATTR_INSTALLATION_TYPE],
        }

        if supervisor_info is not None:
            payload[ATTR_SUPERVISOR] = {
                ATTR_HEALTHY: supervisor_info[ATTR_HEALTHY],
                ATTR_SUPPORTED: supervisor_info[ATTR_SUPPORTED],
                ATTR_ARCH: supervisor_info[ATTR_ARCH],
            }

        if operating_system_info.get(ATTR_BOARD) is not None:
            payload[ATTR_OPERATING_SYSTEM] = {
                ATTR_BOARD: operating_system_info[ATTR_BOARD],
                ATTR_VERSION: operating_system_info[ATTR_VERSION],
            }

        if self.preferences.get(ATTR_USAGE, False) or self.preferences.get(
            ATTR_STATISTICS, False
        ):
            ent_reg = er.async_get(hass)

            try:
                yaml_configuration = await conf_util.async_hass_config_yaml(hass)
            except HomeAssistantError as err:
                LOGGER.error(err)
                return

            configuration_set = _domains_from_yaml_config(yaml_configuration)

            er_platforms = {
                entity.platform
                for entity in ent_reg.entities.values()
                if not entity.disabled
            }

            domains = async_get_loaded_integrations(hass)
            configured_integrations = await async_get_integrations(hass, domains)
            enabled_domains = set(configured_integrations)

            for integration in configured_integrations.values():
                if isinstance(integration, IntegrationNotFound):
                    continue

                if isinstance(integration, BaseException):
                    raise integration

                if not self._async_should_report_integration(
                    integration=integration,
                    yaml_domains=configuration_set,
                    entity_registry_platforms=er_platforms,
                ):
                    continue

                if not integration.is_built_in:
                    custom_integrations.append(
                        {
                            ATTR_DOMAIN: integration.domain,
                            ATTR_VERSION: integration.version,
                        }
                    )
                    continue

                integrations.append(integration.domain)

            if addons_info is not None:
                supervisor_client = hassio.get_supervisor_client(hass)
                installed_addons = await asyncio.gather(
                    *(supervisor_client.addons.addon_info(slug) for slug in addons_info)
                )
                addons.extend(
                    {
                        ATTR_SLUG: addon.slug,
                        ATTR_PROTECTED: addon.protected,
                        ATTR_VERSION: addon.version,
                        ATTR_AUTO_UPDATE: addon.auto_update,
                    }
                    for addon in installed_addons
                )

        if self.preferences.get(ATTR_USAGE, False):
            payload[ATTR_CERTIFICATE] = hass.http.ssl_certificate is not None
            payload[ATTR_INTEGRATIONS] = integrations
            payload[ATTR_CUSTOM_INTEGRATIONS] = custom_integrations
            if supervisor_info is not None:
                payload[ATTR_ADDONS] = addons

            if ENERGY_DOMAIN in enabled_domains:
                payload[ATTR_ENERGY] = {
                    ATTR_CONFIGURED: await energy_is_configured(hass)
                }

            if RECORDER_DOMAIN in enabled_domains:
                instance = get_recorder_instance(hass)
                engine = instance.database_engine
                if engine and engine.version is not None:
                    payload[ATTR_RECORDER] = {
                        ATTR_ENGINE: engine.dialect.value,
                        ATTR_VERSION: engine.version,
                    }

        if self.preferences.get(ATTR_STATISTICS, False):
            payload[ATTR_STATE_COUNT] = hass.states.async_entity_ids_count()
            payload[ATTR_AUTOMATION_COUNT] = hass.states.async_entity_ids_count(
                AUTOMATION_DOMAIN
            )
            payload[ATTR_INTEGRATION_COUNT] = len(integrations)
            if supervisor_info is not None:
                payload[ATTR_ADDON_COUNT] = len(addons)
            payload[ATTR_USER_COUNT] = len(
                [
                    user
                    for user in await hass.auth.async_get_users()
                    if not user.system_generated
                ]
            )

        try:
            async with timeout(30):
                response = await self._session.post(self.endpoint_basic, json=payload)
                if response.status == 200:
                    LOGGER.info(
                        (
                            "Submitted analytics to Home Assistant servers. "
                            "Information submitted includes %s"
                        ),
                        payload,
                    )
                else:
                    LOGGER.warning(
                        "Sending analytics failed with statuscode %s from %s",
                        response.status,
                        self.endpoint_basic,
                    )
        except TimeoutError:
            LOGGER.error("Timeout sending analytics to %s", BASIC_ENDPOINT_URL)
        except aiohttp.ClientError as err:
            LOGGER.error("Error sending analytics to %s: %r", BASIC_ENDPOINT_URL, err)