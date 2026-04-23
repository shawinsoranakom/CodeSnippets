def _async_device_updates_handler(self) -> None:
        """Handle device updates."""
        if not self.device.initialized:
            return

        # For buttons which are battery powered - set initial value for last_event_count
        if self.model in SHBTN_MODELS and self._last_input_events_count.get(1) is None:
            for block in self.device.blocks:
                if block.type != "device":
                    continue

                wakeup_event = cast(list, block.wakeupEvent)
                if len(wakeup_event) == 1 and wakeup_event[0] == "button":
                    self._last_input_events_count[1] = -1

                break

        # Check for input events and config change
        cfg_changed = 0
        for block in self.device.blocks:
            if block.type == "device" and block.cfgChanged is not None:
                cfg_changed = cast(int, block.cfgChanged)

            # Shelly TRV sends information about changing the configuration for no
            # reason, reloading the config entry is not needed for it.
            if self.model == MODEL_VALVE:
                self._last_cfg_changed = None

            # For dual mode bulbs ignore change if it is due to mode/effect change
            if self.model in DUAL_MODE_LIGHT_MODELS:
                if "mode" in block.sensor_ids:
                    if self._last_mode != block.mode:
                        self._last_cfg_changed = None
                    self._last_mode = block.mode

            if self.model in MODELS_SUPPORTING_LIGHT_EFFECTS:
                if "effect" in block.sensor_ids:
                    if self._last_effect != block.effect:
                        self._last_cfg_changed = None
                    self._last_effect = block.effect

            if (
                "inputEvent" not in block.sensor_ids
                or "inputEventCnt" not in block.sensor_ids
            ):
                LOGGER.debug("Skipping non-input event block %s", block.description)
                continue

            channel = int(block.channel or 0) + 1
            event_type = block.inputEvent
            last_event_count = self._last_input_events_count.get(channel)
            self._last_input_events_count[channel] = block.inputEventCnt

            if (
                last_event_count is None
                or last_event_count == block.inputEventCnt
                or event_type == ""
            ):
                LOGGER.debug("Skipping block event %s", event_type)
                continue

            if event_type in INPUTS_EVENTS_DICT:
                for event_callback in self._input_event_listeners:
                    event_callback(
                        {"channel": channel, "event": INPUTS_EVENTS_DICT[event_type]}
                    )
                self.hass.bus.async_fire(
                    EVENT_SHELLY_CLICK,
                    {
                        ATTR_DEVICE_ID: self.device_id,
                        ATTR_DEVICE: self.device.settings["device"]["hostname"],
                        ATTR_CHANNEL: channel,
                        ATTR_CLICK_TYPE: INPUTS_EVENTS_DICT[event_type],
                        ATTR_GENERATION: 1,
                    },
                )

        if self._last_cfg_changed is not None and cfg_changed > self._last_cfg_changed:
            LOGGER.info(
                "Config for %s changed, reloading entry in %s seconds",
                self.name,
                ENTRY_RELOAD_COOLDOWN,
            )
            self._debounced_reload.async_schedule_call()
        self._last_cfg_changed = cfg_changed