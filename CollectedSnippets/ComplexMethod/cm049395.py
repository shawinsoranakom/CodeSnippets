def run(self):
        try:
            for device in self.input_devices:
                for event in device.read_loop():
                    if self._stopped.is_set():
                        break
                    if event.type == evdev.ecodes.EV_KEY:
                        data = evdev.categorize(event)

                        modifier_name = self._scancode_to_modifier.get(data.scancode)
                        if modifier_name:
                            if modifier_name in ('caps_lock', 'num_lock'):
                                if data.keystate == 1:
                                    self._tracked_modifiers[modifier_name] = not self._tracked_modifiers[modifier_name]
                            else:
                                self._tracked_modifiers[modifier_name] = bool(data.keystate)  # 1 for keydown, 0 for keyup
                        elif data.keystate == 1:
                            self.key_input(data.scancode)

        except Exception as err:  # noqa: BLE001
            _logger.warning(err)