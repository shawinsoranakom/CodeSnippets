def write(self, vals):
        # for journals, force a readable name instead of a sanitized name e.g. non ascii in journal names
        if vals.get('alias_name') and 'type' not in vals:
            # will raise if writing name on more than 1 record, using self[0] is safe
            if (not self.env['mail.alias']._is_encodable(vals['alias_name']) or
                not self.env['mail.alias']._sanitize_alias_name(vals['alias_name'])):
                vals['alias_name'] = self._alias_prepare_alias_name(
                    False, vals.get('name', self.name), vals.get('code', self.code), self[0].type, self[0].company_id)

        for journal in self:
            company = journal.company_id
            if ('company_id' in vals and journal.company_id.id != vals['company_id']):
                company = self.env['res.company'].browse(vals['company_id'])
                if journal.bank_account_id.company_id and journal.bank_account_id.company_id != company:
                    journal.bank_account_id.write({
                        'company_id': company.id,
                        'partner_id': company.partner_id.id,
                    })
            if 'currency_id' in vals:
                if journal.bank_account_id:
                    journal.bank_account_id.currency_id = vals['currency_id']
            if 'bank_account_id' in vals:
                if vals.get('bank_account_id'):
                    bank_account = self.env['res.partner.bank'].browse(vals['bank_account_id'])
                    if bank_account.partner_id != company.partner_id:
                        raise UserError(_("The partners of the journal's company and the related bank account mismatch."))
            if 'restrict_mode_hash_table' in vals and not vals.get('restrict_mode_hash_table'):
                domain = self.env['account.move']._get_move_hash_domain(
                    common_domain=[('journal_id', '=', journal.id), ('inalterable_hash', '!=', False)]
                )
                journal_entry = self.env['account.move'].sudo().search_count(domain, limit=1)
                if journal_entry:
                    field_string = self._fields['restrict_mode_hash_table'].get_description(self.env)['string']
                    raise UserError(_("You cannot modify the field %s of a journal that already has accounting entries.", field_string))
        result = super(AccountJournal, self).write(vals)

        # Ensure alias coherency when changing type
        if 'type' in vals and not self.env.context.get('account_journal_skip_alias_sync'):
            for journal in self:
                alias_vals = journal._alias_get_creation_values()
                alias_vals = {
                    'alias_defaults': alias_vals['alias_defaults'],
                    'alias_name': alias_vals['alias_name'],
                }
                journal.update(alias_vals)

        # Ensure the liquidity accounts are sharing the same foreign currency.
        if 'currency_id' in vals:
            for journal in self.filtered(lambda journal: journal.type in ('bank', 'cash', 'credit')):
                journal.default_account_id.currency_id = journal.currency_id

        # Create the bank_account_id if necessary
        if 'bank_acc_number' in vals:
            for journal in self.filtered(lambda r: r.type == 'bank' and not r.bank_account_id):
                journal.set_bank_account(vals.get('bank_acc_number'), vals.get('bank_id'))
        if 'bank_acc_number' in vals or 'bank_account_id' in vals:
            for bank in self.filtered(lambda r: r.type == 'bank').bank_account_id:
                if bank._user_can_trust():
                    bank.allow_out_payment = True
        return result