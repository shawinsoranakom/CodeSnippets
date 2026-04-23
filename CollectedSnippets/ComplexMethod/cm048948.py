def _populate_creation_vals(self, vals_list):
        for vals in vals_list:
            if 'pos_order_line_id' in vals:
                if 'partner_id' not in vals:
                    pol = self.env['pos.order.line'].browse(vals['pos_order_line_id']).exists()
                    if pol and pol.order_id.partner_id:
                        vals['partner_id'] = pol.order_id.partner_id.id
                for field in ["name", "email", "phone", "company_name"]:
                    if field in vals and not vals[field]:
                        vals.pop(field)