def _compute_tax_id(self):
        for wizard in self:
            sections = wizard.related_move_id._get_l10n_in_tds_tcs_applicable_sections()
            if sections:
                accounts_by_section = {}
                for line in wizard.related_move_id.line_ids:
                    section = line.account_id.l10n_in_tds_tcs_section_id
                    if section in sections:
                        accounts_by_section[section] = line.account_id
                tax = self.env['account.tax']
                for section, account in accounts_by_section.items():
                    # Search for the last withhold move line that matches the pan entity and account and section
                    withhold_move_line = self.env['account.move.line'].search([
                        ('move_id.l10n_in_withholding_ref_move_id.commercial_partner_id.l10n_in_pan_entity_id', '=', wizard.related_move_id.commercial_partner_id.l10n_in_pan_entity_id.id),
                        ('move_id.l10n_in_withholding_ref_move_id.line_ids.account_id', 'in', account.id),
                        ('move_id.l10n_in_withholding_ref_move_id.line_ids.l10n_in_tds_tcs_section_id', 'in', section.id),
                        ('move_id.state', '=', 'posted'),
                        ('tax_ids.l10n_in_section_id', '=', section.id),
                    ], limit=1, order='id desc')
                    if withhold_move_line:
                        tax = withhold_move_line.tax_ids.filtered(lambda t: t.l10n_in_section_id == section)
                        break
                if tax:
                    wizard.tax_id = tax