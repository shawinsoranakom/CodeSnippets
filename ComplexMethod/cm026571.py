async def async_call_hmipc_service(service: ServiceCall) -> None:
        """Call correct HomematicIP Cloud service."""
        service_name = service.service

        if service_name == SERVICE_ACTIVATE_ECO_MODE_WITH_DURATION:
            await _async_activate_eco_mode_with_duration(service)
        elif service_name == SERVICE_ACTIVATE_ECO_MODE_WITH_PERIOD:
            await _async_activate_eco_mode_with_period(service)
        elif service_name == SERVICE_ACTIVATE_VACATION:
            await _async_activate_vacation(service)
        elif service_name == SERVICE_DEACTIVATE_ECO_MODE:
            await _async_deactivate_eco_mode(service)
        elif service_name == SERVICE_DEACTIVATE_VACATION:
            await _async_deactivate_vacation(service)
        elif service_name == SERVICE_DUMP_HAP_CONFIG:
            await _async_dump_hap_config(service)
        elif service_name == SERVICE_RESET_ENERGY_COUNTER:
            await _async_reset_energy_counter(service)
        elif service_name == SERVICE_SET_ACTIVE_CLIMATE_PROFILE:
            await _set_active_climate_profile(service)
        elif service_name == SERVICE_SET_HOME_COOLING_MODE:
            await _async_set_home_cooling_mode(service)