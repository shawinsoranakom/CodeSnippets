def _show_autopost_bills_wizard(self):
        if (
            len(self) != 1
            or self.state != "posted"
            or not self.is_purchase_document(include_receipts=True)
            or self.restrict_mode_hash_table
            or all(not l.is_imported for l in self.line_ids)
            or not self.partner_id
            or self.partner_id.autopost_bills != "ask"
            or not self.company_id.autopost_bills
            or self.is_manually_modified
        ):
            return False
        prev_bills_same_partner = self.search([
            ('id', '!=', self.id),
            ('partner_id', '=', self.partner_id.id),
            ('state', '=', 'posted'),
            ('move_type', 'in', self.get_purchase_types(include_receipts=True)),
        ], order="create_date DESC", limit=10)
        nb_unmodified_bills = 1  # +1 for current bill that hasn't been modified either
        for move in prev_bills_same_partner:
            if move.is_manually_modified:
                break
            nb_unmodified_bills += 1
        if nb_unmodified_bills < 3:
            return False
        wizard = self.env['account.autopost.bills.wizard'].create({
            'partner_id': self.partner_id.id,
            'nb_unmodified_bills': nb_unmodified_bills,
        })
        return {
            'name': _("Autopost Bills"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.autopost.bills.wizard',
            'res_id': wizard.id,
            'views': [(False, 'form')],
            'target': 'new',
        }