def action_close_stock_valuation(self, at_date=None, auto_post=False):
        self.ensure_one()
        if at_date and isinstance(at_date, str):
            at_date = fields.Date.from_string(at_date)
        last_closing_date = self._get_last_closing_date()
        if at_date and last_closing_date and at_date < fields.Date.to_date(last_closing_date):
            raise UserError(self.env._('It exists closing entries after the selected date. Cancel them before generate an entry prior to them'))
        aml_vals_list = self._action_close_stock_valuation(at_date=at_date)

        if not aml_vals_list:
            # No account moves to create, so nothing to display.
            raise UserError(_("Everything is correctly closed"))
        if not self.account_stock_journal_id:
            raise UserError(self.env._("Please set the Journal for Inventory Valuation in the settings."))
        if not self.account_stock_valuation_id:
            raise UserError(self.env._("Please set the Valuation Account for Inventory Valuation in the settings."))

        moves_vals = {
            'journal_id': self.account_stock_journal_id.id,
            'date': at_date or fields.Date.today(),
            'ref': _('Stock Closing'),
            'line_ids': [Command.create(aml_vals) for aml_vals in aml_vals_list],
        }
        account_move = self.env['account.move'].create(moves_vals)
        self._save_closing_id(account_move.id)
        if auto_post:
            account_move._post()

        return {
            'type': 'ir.actions.act_window',
            'name': _("Journal Items"),
            'res_model': 'account.move',
            'res_id': account_move.id,
            'views': [(False, 'form')],
        }