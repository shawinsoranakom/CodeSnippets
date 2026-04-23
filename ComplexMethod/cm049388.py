def usb_matcher(dev):
        # USB Class codes documentation: https://www.usb.org/defined-class-codes
        # Ignore USB hubs (9) and printers (7)
        if dev.bDeviceClass in [7, 9]:
            return False
        # If the device has generic base class (0) check its interface descriptor
        elif dev.bDeviceClass == 0:
            for conf in dev:
                for interface in conf:
                    if interface.bInterfaceClass == 7:  # 7 = printer
                        return False

        # Ignore serial adapters
        try:
            return dev.product != "USB2.0-Ser!"
        except ValueError:
            return True
        except core.USBError:  # Thrown for some printers like POS80D
            return False