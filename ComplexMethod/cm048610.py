def _compute_payment_method_line_id(self):
        ''' Compute the 'payment_method_line_id' field.
        This field is not computed in '_compute_payment_method_line_fields' because it's a stored editable one.
        '''
        for pay in self:
            available_payment_method_lines = pay.available_payment_method_line_ids
            inbound_payment_method = pay.partner_id.property_inbound_payment_method_line_id
            outbound_payment_method = pay.partner_id.property_outbound_payment_method_line_id
            if pay.payment_type == 'inbound' and inbound_payment_method.id in available_payment_method_lines.ids:
                pay.payment_method_line_id = inbound_payment_method
            elif pay.payment_type == 'outbound' and outbound_payment_method.id in available_payment_method_lines.ids:
                pay.payment_method_line_id = outbound_payment_method
            elif pay.payment_method_line_id.id in available_payment_method_lines.ids:
                pay.payment_method_line_id = pay.payment_method_line_id
            elif available_payment_method_lines:
                pay.payment_method_line_id = available_payment_method_lines[0]._origin
            else:
                pay.payment_method_line_id = False