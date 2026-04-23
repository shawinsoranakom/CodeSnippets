def write(self, vals):
        has_been_posted = False
        for order in self:
            if order.company_id._is_accounting_unalterable():
                # write the hash and the secure_sequence_number when posting or invoicing an pos.order
                if vals.get('state') in ['paid', 'done']:
                    has_been_posted = True

                # restrict the operation in case we are trying to write a forbidden field
                if order.pos_version:
                    ORDER_FIELDS = ORDER_FIELDS_FROM_17_4
                else:
                    ORDER_FIELDS = ORDER_FIELDS_BEFORE_17_4
                if (order.state in ['paid', 'done'] and set(vals).intersection(ORDER_FIELDS)):
                    raise UserError(_('According to the French law, you cannot modify a point of sale order. Forbidden fields: %s.') % ', '.join(ORDER_FIELDS))
                # restrict the operation in case we are trying to overwrite existing hash
                if (order.l10n_fr_hash and 'l10n_fr_hash' in vals) or (order.l10n_fr_secure_sequence_number and 'l10n_fr_secure_sequence_number' in vals):
                    raise UserError(_('You cannot overwrite the values ensuring the inalterability of the point of sale.'))
        res = super().write(vals)
        # write the hash and the secure_sequence_number when posting or invoicing a pos order
        if has_been_posted:
            for order in self.filtered(lambda o: o.company_id._is_accounting_unalterable() and
                                                not (o.l10n_fr_secure_sequence_number or o.l10n_fr_hash)):
                new_number = order.company_id.l10n_fr_pos_cert_sequence_id.next_by_id()
                res |= super(PosOrder, order).write({'l10n_fr_secure_sequence_number': new_number})
                res |= super(PosOrder, order).write({'l10n_fr_hash': order._get_new_hash()})
        return res