def value_changed(self, telegram: ERP1Telegram) -> None:
        """Fire an event with the data that have changed.

        This method is called when there is an incoming packet associated
        with this platform.
        """
        if not self.address:
            return
        # Energy Bow
        pushed = None

        if telegram.status == 0x30:
            pushed = 1
        elif telegram.status == 0x20:
            pushed = 0

        self.schedule_update_ha_state()

        action = telegram.telegram_data[0]
        if action == 0x70:
            self.which = 0
            self.onoff = 0
        elif action == 0x50:
            self.which = 0
            self.onoff = 1
        elif action == 0x30:
            self.which = 1
            self.onoff = 0
        elif action == 0x10:
            self.which = 1
            self.onoff = 1
        elif action == 0x37:
            self.which = 10
            self.onoff = 0
        elif action == 0x15:
            self.which = 10
            self.onoff = 1
        self.hass.bus.fire(
            EVENT_BUTTON_PRESSED,
            {
                "id": self.address.to_bytelist(),
                "pushed": pushed,
                "which": self.which,
                "onoff": self.onoff,
            },
        )