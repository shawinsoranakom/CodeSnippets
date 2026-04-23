def action_add_to_po(self):
        aml_ids = [abs(record_id) for record_id in self.env.context.get('active_ids') if record_id < 0]
        lines_to_add = self.env['account.move.line'].browse(aml_ids).filtered(lambda l: l.product_id)
        if not lines_to_add:
            raise UserError(_("There are no products to add to the Purchase Order. Are these Down Payments?"))
        line_vals = lines_to_add._prepare_line_values_for_purchase()
        if self.purchase_order_id:
            new_po_lines = self.env['purchase.order.line'].create([{
                **val,
                'order_id': self.purchase_order_id.id,
            } for val in line_vals])
            self.purchase_order_id.order_line += new_po_lines
        else:
            self.purchase_order_id = self.env['purchase.order'].create({
                'partner_id': lines_to_add.partner_id.id,
                'order_line': [Command.create(val) for val in line_vals],
            })
            new_po_lines = self.purchase_order_id.order_line

        self.purchase_order_id.button_confirm()
        for aml, pol in zip(lines_to_add, new_po_lines):
            if aml.product_id == pol.product_id:
                aml.purchase_line_id = pol.id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': self.purchase_order_id.id,
        }