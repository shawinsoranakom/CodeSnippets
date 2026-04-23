def update(self) -> None:
        """Communicate with a Lightwave RTF Proxy to get state."""
        (temp, targ, _, trv_output) = self._lwlink.read_trv_status(self._serial)
        if temp is not None:
            self._attr_current_temperature = temp
        if targ is not None:
            if self._inhibit == 0:
                self._attr_target_temperature = targ
                if targ == 0:
                    # TRV off
                    self._attr_target_temperature = None
                if targ >= 40:
                    # Call for heat mode, or TRV in a fixed position
                    self._attr_target_temperature = None
            else:
                # Done the job - use proxy next iteration
                self._inhibit = 0
        if trv_output is not None:
            if trv_output > 0:
                self._attr_hvac_action = HVACAction.HEATING
            else:
                self._attr_hvac_action = HVACAction.OFF