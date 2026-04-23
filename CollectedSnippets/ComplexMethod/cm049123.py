def action_add_downpayment(self):
        aml_ids = [abs(record_id) for record_id in self.env.context.get('active_ids') if record_id < 0]
        lines_to_convert = self.env['account.move.line'].browse(aml_ids)
        context = {'lang': lines_to_convert.partner_id.lang}
        if not self.purchase_order_id:
            self.purchase_order_id = self.env['purchase.order'].create({
                'partner_id': lines_to_convert.partner_id.id,
            })
        po_currency = self.purchase_order_id.currency_id
        company = self.purchase_order_id.company_id
        date = self.purchase_order_id.date_order or fields.Date.today()
        line_vals = [
            {
                'name': _("Down Payment (ref: %(ref)s)", ref=aml.display_name),
                'product_qty': 0.0,
                'product_uom_id': aml.product_uom_id.id,
                'is_downpayment': True,
                'price_unit': aml.currency_id._convert(aml.price_unit, po_currency, company, date) if aml.currency_id != po_currency else aml.price_unit,
                'tax_ids': aml.tax_ids,
                'order_id': self.purchase_order_id.id,
            }
            for aml in lines_to_convert
        ]
        del context

        downpayment_lines = self.purchase_order_id._create_downpayments(line_vals)
        for aml, dpl in zip(lines_to_convert, downpayment_lines):
            aml.purchase_line_id = dpl.id

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': self.purchase_order_id.id,
        }