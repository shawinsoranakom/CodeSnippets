def create(self, vals_list):
        # EXTENDS base res.partner.bank
        to_trust = [vals.get('allow_out_payment') for vals in vals_list]
        for vals in vals_list:
            vals['allow_out_payment'] = False

        for vals in vals_list:
            if (partner_id := vals.get('partner_id')) and (acc_number := vals.get('acc_number')):
                archived_res_partner_bank = self.env['res.partner.bank'].search([('active', '=', False), ('partner_id', '=', partner_id), ('acc_number', '=', acc_number)])
                if archived_res_partner_bank:
                    raise UserError(_("A bank account with Account Number %(number)s already exists for Partner %(partner)s, but is archived. Please unarchive it instead.", number=acc_number, partner=archived_res_partner_bank.partner_id.name))

        accounts = super().create(vals_list)
        for account, trust in zip(accounts, to_trust):
            if trust and account._user_can_trust():
                account.allow_out_payment = True
            msg = _("Bank Account %s created", account._get_html_link(title=f"#{account.id}"))
            account.partner_id._message_log(body=msg)
        return accounts