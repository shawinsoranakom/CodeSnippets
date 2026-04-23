def build_devices_mock(devices: Devices):
        device_list = []
        if devices.data is None:
            return device_list
        for device_data in devices.data.devices:
            device = AsyncMock(spec=Device)
            device.data = device_data
            device.id = device.data.id
            device.name = device.data.name
            device.is_on = device.data.features.switchable.status
            device.brightness = (
                device.data.features.dimmable.status
                if device.data.features.dimmable
                else None
            )
            device.color_temperature = (
                device.data.features.color_kelvin.status
                if device.data.features.color_kelvin
                else None
            )
            device.rgb_color = (
                (
                    device.data.features.color_rgb.status.red,
                    device.data.features.color_rgb.status.green,
                    device.data.features.color_rgb.status.blue,
                )
                if device.data.features.color_rgb
                else None
            )
            device.rgbw_color = (
                (
                    device.data.features.color_rgb.status.red,
                    device.data.features.color_rgb.status.green,
                    device.data.features.color_rgb.status.blue,
                    device.data.features.color_waf.status.white,
                )
                if device.data.features.color_rgb and device.data.features.color_waf
                else None
            )
            device_list.append(device)
        return device_list