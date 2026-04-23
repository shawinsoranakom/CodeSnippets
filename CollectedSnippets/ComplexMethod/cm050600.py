def _l10n_it_edi_doi_check_configuration(self):
        """
        Raise a UserError in case the configuration of the sale order is invalid.
        """
        errors = []
        for order in self:
            declaration = order.l10n_it_edi_doi_id
            if declaration:
                validity_warnings = declaration._get_validity_warnings(
                    order.company_id, order.partner_id.commercial_partner_id, order.currency_id, order.l10n_it_edi_doi_date,
                    only_blocking=True, sales_order=True,
                )
                errors.extend(validity_warnings)

            declaration_of_intent_tax = order.company_id.l10n_it_edi_doi_tax_id
            if not declaration_of_intent_tax:
                continue
            declaration_tax_lines = order.order_line.filtered(
                lambda line: declaration_of_intent_tax in line.tax_ids
            )
            if declaration_tax_lines and not order.l10n_it_edi_doi_id:
                errors.append(_('Given the tax %s is applied, there should be a Declaration of Intent selected.',
                                declaration_of_intent_tax.name))
            if any(line.tax_ids != declaration_of_intent_tax for line in declaration_tax_lines):
                errors.append(_('A line using tax %s should not contain any other taxes',
                                declaration_of_intent_tax.name))
        if errors:
            raise UserError('\n'.join(errors))