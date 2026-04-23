def assert_update_switch_port(
        device: OmadaSwitch,
        switch_port_details: OmadaSwitchPortDetails,
        poe_enabled: bool,
        settings: SwitchPortSettings,
    ) -> None:
        assert device
        assert device.mac == network_switch_mac
        assert switch_port_details
        assert switch_port_details.port == port_num
        assert settings
        assert settings.profile_override_enabled
        assert settings.profile_overrides
        assert settings.profile_overrides.enable_poe == poe_enabled