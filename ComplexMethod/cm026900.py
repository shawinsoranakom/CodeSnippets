def _get_data(self) -> dict[str, Any]:
        """Get new sensor data for Wallbox component."""
        try:
            data: dict[str, Any] = self._wallbox.getChargerStatus(self._station)
            data[CHARGER_MAX_CHARGING_CURRENT_KEY] = data[CHARGER_DATA_KEY][
                CHARGER_MAX_CHARGING_CURRENT_KEY
            ]
            data[CHARGER_LOCKED_UNLOCKED_KEY] = data[CHARGER_DATA_KEY][
                CHARGER_LOCKED_UNLOCKED_KEY
            ]
            data[CHARGER_ENERGY_PRICE_KEY] = data[CHARGER_DATA_KEY][
                CHARGER_ENERGY_PRICE_KEY
            ]
            # Only show max_icp_current if power_boost is available in the wallbox unit:
            if (
                data[CHARGER_DATA_KEY].get(CHARGER_MAX_ICP_CURRENT_KEY, 0) > 0
                and CHARGER_POWER_BOOST_KEY
                in data[CHARGER_DATA_KEY][CHARGER_PLAN_KEY][CHARGER_FEATURES_KEY]
            ):
                data[CHARGER_MAX_ICP_CURRENT_KEY] = data[CHARGER_DATA_KEY][
                    CHARGER_MAX_ICP_CURRENT_KEY
                ]

            data[CHARGER_CURRENCY_KEY] = (
                f"{data[CHARGER_DATA_KEY][CHARGER_CURRENCY_KEY][CODE_KEY]}/kWh"
            )

            data[CHARGER_STATUS_DESCRIPTION_KEY] = CHARGER_STATUS.get(
                data[CHARGER_STATUS_ID_KEY], ChargerStatus.UNKNOWN
            )

            # Set current solar charging mode
            eco_smart_enabled = (
                data[CHARGER_DATA_KEY]
                .get(CHARGER_ECO_SMART_KEY, {})
                .get(CHARGER_ECO_SMART_STATUS_KEY)
            )

            eco_smart_mode = (
                data[CHARGER_DATA_KEY]
                .get(CHARGER_ECO_SMART_KEY, {})
                .get(CHARGER_ECO_SMART_MODE_KEY)
            )
            if eco_smart_mode is None:
                data[CHARGER_ECO_SMART_KEY] = EcoSmartMode.DISABLED
            elif eco_smart_enabled is False:
                data[CHARGER_ECO_SMART_KEY] = EcoSmartMode.OFF
            elif eco_smart_mode == 0:
                data[CHARGER_ECO_SMART_KEY] = EcoSmartMode.ECO_MODE
            elif eco_smart_mode == 1:
                data[CHARGER_ECO_SMART_KEY] = EcoSmartMode.FULL_SOLAR
            return data  # noqa: TRY300
        except requests.exceptions.HTTPError as wallbox_connection_error:
            if wallbox_connection_error.response.status_code == 429:
                raise UpdateFailed(
                    translation_domain=DOMAIN, translation_key="too_many_requests"
                ) from wallbox_connection_error
            raise UpdateFailed(
                translation_domain=DOMAIN, translation_key="api_failed"
            ) from wallbox_connection_error