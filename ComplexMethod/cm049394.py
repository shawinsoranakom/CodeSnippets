def __init__(self, identifier, device):
        if not hasattr(KeyboardUSBDriver, 'display'):
            os.environ['XAUTHORITY'] = "/run/lightdm/pi/xauthority"
            KeyboardUSBDriver.display = xlib.XOpenDisplay(bytes(":0.0", "utf-8"))

        super().__init__(identifier, device)
        self.device_connection = 'direct'
        self.device_name = self._set_name()

        self._actions.update({
            'update_layout': self._update_layout,
            'update_is_scanner': self._save_is_scanner,
            '': self._action_default,
        })

        # from https://github.com/xkbcommon/libxkbcommon/blob/master/test/evdev-scancodes.h
        self._scancode_to_modifier = {
            42: 'left_shift',
            54: 'right_shift',
            58: 'caps_lock',
            69: 'num_lock',
            100: 'alt_gr',  # right alt
        }
        self._tracked_modifiers = {modifier: False for modifier in self._scancode_to_modifier.values()}

        if not KeyboardUSBDriver.available_layouts:
            KeyboardUSBDriver.load_layouts_list()
        KeyboardUSBDriver.send_layouts_list()

        for evdev_device in [evdev.InputDevice(path) for path in evdev.list_devices()]:
            if (device.idVendor == evdev_device.info.vendor) and (device.idProduct == evdev_device.info.product):
                self.input_devices.append(evdev_device)

        self._set_device_type('scanner') if self._is_scanner() else self._set_device_type()