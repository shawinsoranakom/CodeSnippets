def default_get(self, fields):
        result = super().default_get(fields)
        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids', [])
        if active_model not in ('account.move', 'account.payment') or not active_ids:
            raise UserError(_("TDS must be created from an Invoice or a Payment."))
        if len(active_ids) > 1:
            raise UserError(_("You can only create a withhold for only one record at a time."))
        active_record = self.env[active_model].browse(active_ids)
        result['reference'] = _("TDS of %s", active_record.name)
        if active_model == 'account.move':
            if active_record.move_type not in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund') or active_record.state != 'posted':
                raise UserError(_("TDS must be created from Posted Customer Invoices, Customer Credit Notes, Vendor Bills or Vendor Refunds."))
            result['related_move_id'] = active_record.id
        elif active_model == 'account.payment':
            if not active_record.partner_id:
                type_name = _("Vendor Payment") if active_record.partner_type == 'supplier' else _("Customer Payment")
                raise UserError(_("Please set a partner on the %s before creating a withhold.", type_name))
            result['related_payment_id'] = active_record.id
        return result