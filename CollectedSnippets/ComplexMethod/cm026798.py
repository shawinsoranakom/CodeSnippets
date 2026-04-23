def __init__(self, *args: Any) -> None:
        """Initialize a SecuritySystem accessory object."""
        super().__init__(*args, category=CATEGORY_ALARM_SYSTEM)
        state = self.hass.states.get(self.entity_id)
        assert state
        self._alarm_code = self.config.get(ATTR_CODE)

        supported_states = state.attributes.get(
            ATTR_SUPPORTED_FEATURES,
            (
                AlarmControlPanelEntityFeature.ARM_HOME
                | AlarmControlPanelEntityFeature.ARM_VACATION
                | AlarmControlPanelEntityFeature.ARM_AWAY
                | AlarmControlPanelEntityFeature.ARM_NIGHT
                | AlarmControlPanelEntityFeature.TRIGGER
            ),
        )

        serv_alarm = self.add_preload_service(SERV_SECURITY_SYSTEM)
        current_char = serv_alarm.get_characteristic(CHAR_CURRENT_SECURITY_STATE)
        target_char = serv_alarm.get_characteristic(CHAR_TARGET_SECURITY_STATE)
        default_current_states = current_char.properties.get("ValidValues")
        default_target_services = target_char.properties.get("ValidValues")

        current_supported_states = [HK_ALARM_DISARMED, HK_ALARM_TRIGGERED]
        target_supported_services = [HK_ALARM_DISARMED]

        if supported_states & AlarmControlPanelEntityFeature.ARM_HOME:
            current_supported_states.append(HK_ALARM_STAY_ARMED)
            target_supported_services.append(HK_ALARM_STAY_ARMED)

        if supported_states & (
            AlarmControlPanelEntityFeature.ARM_AWAY
            | AlarmControlPanelEntityFeature.ARM_VACATION
        ):
            current_supported_states.append(HK_ALARM_AWAY_ARMED)
            target_supported_services.append(HK_ALARM_AWAY_ARMED)

        if supported_states & AlarmControlPanelEntityFeature.ARM_NIGHT:
            current_supported_states.append(HK_ALARM_NIGHT_ARMED)
            target_supported_services.append(HK_ALARM_NIGHT_ARMED)

        self.char_current_state = serv_alarm.configure_char(
            CHAR_CURRENT_SECURITY_STATE,
            value=HASS_TO_HOMEKIT_CURRENT[AlarmControlPanelState.DISARMED],
            valid_values={
                key: val
                for key, val in default_current_states.items()
                if val in current_supported_states
            },
        )
        self.char_target_state = serv_alarm.configure_char(
            CHAR_TARGET_SECURITY_STATE,
            value=HASS_TO_HOMEKIT_SERVICES[SERVICE_ALARM_DISARM],
            valid_values={
                key: val
                for key, val in default_target_services.items()
                if val in target_supported_services
            },
            setter_callback=self.set_security_state,
        )

        # Set the state so it is in sync on initial
        # GET to avoid an event storm after homekit startup
        self.async_update_state(state)