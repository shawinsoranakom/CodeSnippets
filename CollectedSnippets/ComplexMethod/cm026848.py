def value_changed(self, telegram: ERP1Telegram) -> None:
        """Update the internal state of the switch."""
        if telegram.rorg == 0xA5:
            # power meter telegram, turn on if > 1 watts
            if (eep := EEP_SPECIFICATIONS.get(EEP(0xA5, 0x12, 0x01))) is None:
                LOGGER.warning("EEP A5-12-01 cannot be decoded")
                return

            msg: EEPMessage = EEPHandler(eep).decode(telegram)

            if "DT" in msg.values and msg.values["DT"].raw == 1:
                # this packet reports the current value
                raw_val = msg.values["MR"].raw
                divisor = msg.values["DIV"].raw
                watts = raw_val / (10**divisor)
                if watts > 1:
                    self._attr_is_on = True
                    self.schedule_update_ha_state()

        elif telegram.rorg == 0xD2:
            # actuator status telegram
            if (eep := EEP_SPECIFICATIONS.get(EEP(0xD2, 0x01, 0x01))) is None:
                LOGGER.warning("EEP D2-01-01 cannot be decoded")
                return

            msg = EEPHandler(eep).decode(telegram)
            if msg.values["CMD"].raw == 4:
                channel = msg.values["I/O"].raw
                output = msg.values["OV"].raw
                if channel == self.channel:
                    self._attr_is_on = output > 0
                    self.schedule_update_ha_state()