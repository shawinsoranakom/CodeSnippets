def __init__(self, identifier, device):
        super().__init__(identifier, device)
        self.conn = Connection()
        self.cups_lock = Lock()
        self.device_connection = device['device-class'].lower()
        self.receipt_protocol = 'star' if 'STR_T' in device['device-id'] else 'escpos'
        self.connected_by_usb = self.device_connection == 'direct'
        self.device_name = device['device-make-and-model']
        self.ip = device.get('ip')

        if any(cmd in device['device-id'] for cmd in ['CMD:STAR;', 'CMD:ESC/POS;']) or "tm-m30" in self.device_name.lower():
            self.device_subtype = "receipt_printer"
        elif any(cmd in device['device-id'] for cmd in ['COMMAND SET:ZPL;', 'CMD:ESCLABEL;']) or "zpl" in self.device_name.lower():
            self.device_subtype = "label_printer"
        else:
            self.device_subtype = "office_printer"

        self.print_status()