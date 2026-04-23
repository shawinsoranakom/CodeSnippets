def receive_report(self, status: dict[OpenThermDataSource, dict]):
        """Receive and handle a new report from the Gateway."""
        ch_active = status[OpenThermDataSource.BOILER].get(gw_vars.DATA_SLAVE_CH_ACTIVE)
        flame_on = status[OpenThermDataSource.BOILER].get(gw_vars.DATA_SLAVE_FLAME_ON)
        cooling_active = status[OpenThermDataSource.BOILER].get(
            gw_vars.DATA_SLAVE_COOLING_ACTIVE
        )
        if ch_active and flame_on:
            self._attr_hvac_action = HVACAction.HEATING
            self._attr_hvac_mode = HVACMode.HEAT
            self._attr_hvac_modes = [HVACMode.HEAT]
        elif cooling_active:
            self._attr_hvac_action = HVACAction.COOLING
            self._attr_hvac_mode = HVACMode.COOL
            self._attr_hvac_modes = [HVACMode.COOL]
        else:
            self._attr_hvac_action = HVACAction.IDLE

        self._attr_current_temperature = status[OpenThermDataSource.THERMOSTAT].get(
            gw_vars.DATA_ROOM_TEMP
        )
        temp_upd = status[OpenThermDataSource.THERMOSTAT].get(
            gw_vars.DATA_ROOM_SETPOINT
        )

        if self._target_temperature != temp_upd:
            self._new_target_temperature = None
        self._target_temperature = temp_upd

        # GPIO mode 5: 0 == Away
        # GPIO mode 6: 1 == Away
        gpio_a_state = status[OpenThermDataSource.GATEWAY].get(gw_vars.OTGW_GPIO_A)
        gpio_b_state = status[OpenThermDataSource.GATEWAY].get(gw_vars.OTGW_GPIO_B)
        self._away_mode_a = gpio_a_state - 5 if gpio_a_state in (5, 6) else None
        self._away_mode_b = gpio_b_state - 5 if gpio_b_state in (5, 6) else None
        self._away_state_a = (
            (
                status[OpenThermDataSource.GATEWAY].get(gw_vars.OTGW_GPIO_A_STATE)
                == self._away_mode_a
            )
            if self._away_mode_a is not None
            else False
        )
        self._away_state_b = (
            (
                status[OpenThermDataSource.GATEWAY].get(gw_vars.OTGW_GPIO_B_STATE)
                == self._away_mode_b
            )
            if self._away_mode_b is not None
            else False
        )
        self.async_write_ha_state()