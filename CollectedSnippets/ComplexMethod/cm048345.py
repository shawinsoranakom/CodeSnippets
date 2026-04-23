def _check_transporter(self):
        error_message = []
        transporter = self.transporter_id
        if transporter and not transporter.check_vat_in(transporter.vat) and (self.mode != "1" or not self.vehicle_no):
            error_message.append(_("- Transporter %s does not have a valid GST Number", transporter.name))
        if self.mode == "4" and self.vehicle_no and self.vehicle_type == "R":
            error_message.append(_("- Vehicle type can not be regular when the transportation mode is ship"))
        return error_message