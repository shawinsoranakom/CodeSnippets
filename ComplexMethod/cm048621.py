def write(self, vals):
        if 'parent_id' in vals:
            partner2move_lines = self.sudo().env['account.move.line'].search([('partner_id', 'in', self.ids)]).grouped('partner_id')
            parent_vat = self.env['res.partner'].browse(vals['parent_id']).vat
            if partner2move_lines and vals['parent_id'] and any((partner.vat or '') != (parent_vat or '') for partner in self):
                raise UserError(_("You cannot set a partner as an invoicing address of another if they have a different %(vat_label)s.", vat_label=self.vat_label))

        res = super().write(vals)

        if 'parent_id' in vals:
            for partner, move_lines in partner2move_lines.items():
                partner._compute_commercial_partner()
                # Make sure to write on all the lines at the same time to avoid breaking the reconciliation check
                move_lines.with_context(bypass_lock_check=BYPASS_LOCK_CHECK).partner_id = partner.commercial_partner_id

                # Update the commercial partner on account.move that were *entirely* dedicated to that partner (exclude moves shared between partners, e.g misc entries or batch bank payments)
                move_lines.move_id.filtered(lambda m: m.partner_id == partner).with_context(bypass_lock_check=BYPASS_LOCK_CHECK).commercial_partner_id = partner.commercial_partner_id
                partner._message_log(body=_("The commercial partner has been updated for all related accounting entries."))
        return res