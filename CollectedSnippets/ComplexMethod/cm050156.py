def _onchange_partner_journal(self):
        """ This method is used when the invoice is created from the sale or subscription """
        expo_journals = ['FEERCEL', 'FEEWS', 'FEERCELP']
        for rec in self.filtered(lambda x: x.company_id.account_fiscal_country_id.code == "AR" and x.journal_id.type == 'sale'
                                 and x.l10n_latam_use_documents and x.partner_id.l10n_ar_afip_responsibility_type_id):
            res_code = rec.partner_id.l10n_ar_afip_responsibility_type_id.code
            domain = [
                *self.env['account.journal']._check_company_domain(rec.company_id),
                ('l10n_latam_use_documents', '=', True),
                ('type', '=', 'sale'),
            ]
            journal = self.env['account.journal']
            msg = False
            if res_code in ['8', '9', '10'] and rec.journal_id.l10n_ar_afip_pos_system not in expo_journals:
                # if it is a foreign partner and journal is not for expo, we try to change it to an expo journal
                journal = journal.search(domain + [('l10n_ar_afip_pos_system', 'in', expo_journals)], limit=1)
                msg = _('You are trying to create an invoice for foreign partner but you don\'t have an exportation journal')
            elif res_code not in ['8', '9', '10'] and rec.journal_id.l10n_ar_afip_pos_system in expo_journals:
                # if it is NOT a foreign partner and journal is for expo, we try to change it to a local journal
                journal = journal.search(domain + [('l10n_ar_afip_pos_system', 'not in', expo_journals)], limit=1)
                msg = _('You are trying to create an invoice for domestic partner but you don\'t have a domestic market journal')
            if journal:
                rec.journal_id = journal.id
            elif msg:
                # Throw an error to user in order to proper configure the journal for the type of operation
                action = self.env.ref('account.action_account_journal_form')
                raise RedirectWarning(msg, action.id, _('Go to Journals'))