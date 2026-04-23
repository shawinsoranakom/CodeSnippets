def _check_record_values(self, vals):
        errors = []

        company_NIF = vals['company'].partner_id._l10n_es_edi_verifactu_get_values().get('NIF')
        if not company_NIF or len(company_NIF) != 9:  # NIFType
            errors.append(_("The NIF '%(company_NIF)s' of the company is not exactly 9 characters long.",
                            company_NIF=company_NIF))

        if not vals['name'] or len(vals['name']) > 60:
            errors.append(_("The name of the record is not between 1 and 60 characters long: %(name)s.",
                            name=vals['name']))

        if vals['documents'] and vals['documents']._filter_waiting():
            errors.append(_("We are waiting to send a Veri*Factu record to the AEAT already."))

        verifactu_registered = vals['verifactu_state'] in ('registered_with_errors', 'accepted')
        # We currently do not support updating registered records (resending).
        if not vals['cancellation'] and verifactu_registered:
            errors.append(_("The record is Veri*Factu registered already."))
        # We currently do not support cancelling records that are not registered or were registered outside odoo.
        if vals['cancellation'] and not verifactu_registered:
            errors.append(_("The cancelled record is not Veri*Factu registered (inside Odoo)."))

        certificate = vals['company'].sudo()._l10n_es_edi_verifactu_get_certificate()
        if not certificate:
            errors.append(_("There is no certificate configured for Veri*Factu on the company."))

        if not vals['invoice_date']:
            errors.append(_("The invoice date is missing."))

        if vals['verifactu_move_type'] == 'correction_substitution' and not vals['substituted_document']:
            errors.append(_("There is no Veri*Factu document for the substituted record."))

        if vals['verifactu_move_type'] == 'correction_substitution' and not vals['substituted_document_reversal_document']:
            errors.append(_("There is no Veri*Factu document for the reversal of the substituted record."))

        if vals['verifactu_move_type'] in ('correction_incremental', 'reversal_for_substitution') and not vals['refunded_document']:
            errors.append(_("There is no Veri*Factu document for the refunded record."))

        need_refund_reason = vals['verifactu_move_type'] in ('correction_incremental', 'correction_substitution')
        if need_refund_reason and not vals['refund_reason']:
            errors.append(_("The refund reason is not specified."))

        simplified_partner = self.env.ref('l10n_es.partner_simplified', raise_if_not_found=False)
        partner_specified = vals['partner'] and vals['partner'] != simplified_partner
        if need_refund_reason and vals['refund_reason'] != 'R5' and vals['is_simplified']:
            errors.append(_("A refund with Refund Reason %(refund_reason)s is not simplified (it needs a partner).",
                            refund_reason=vals['refund_reason']))

        if vals['verifactu_move_type'] == 'invoice' and not partner_specified and not vals['is_simplified']:
            errors.append(_("A non-simplified invoice needs a partner."))

        if not vals['l10n_es_applicability']:
            errors.append(_("Missing Veri*Factu Tax Applicability (Impuesto)."))

        if vals['l10n_es_applicability'] in ('01', '03') and not vals['clave_regimen']:
            errors.append(_("Missing Veri*Factu Regime Key (ClaveRegimen)."))

        sujeto_tax_types = self.env['account.tax']._l10n_es_get_sujeto_tax_types()
        ignored_tax_types = ['ignore', 'retencion']
        supported_tax_types = sujeto_tax_types + ignored_tax_types + ['no_sujeto', 'no_sujeto_loc', 'recargo', 'exento']
        tax_type_description = self.env['account.tax']._fields['l10n_es_type'].get_description(self.env)
        if not vals['tax_details']['tax_details']:
            errors.append(_("There are no taxes set on the invoice"))
        for key, tax_detail in vals['tax_details']['tax_details'].items():
            tax_type = key['l10n_es_type']
            if tax_type not in supported_tax_types:
                # tax_type in ('no_deducible', 'dua')
                # The remaining tax types are purchase taxes (for vendor bills).
                errors.append(_("A tax with value '%(tax_type)s' as %(field)s is not supported.",
                                field=tax_type_description['string'],
                                tax_type=dict(tax_type_description['selection'])[tax_type]))
            elif tax_type in ('no_sujeto', 'no_sujeto_loc'):
                tax_percentage = key['amount']
                tax_amount = tax_detail['tax_amount']
                if float_round(tax_percentage, precision_digits=2) or float_round(tax_amount, precision_digits=2):
                    errors.append(_("No Sujeto VAT taxes must have 0 amount."))
            if len(key['recargo_taxes']) > 1:
                errors.append(_("Only a single recargo tax may be used per \"main\" tax."))

        main_tax_types = self.env['account.tax']._l10n_es_get_main_tax_types()
        tax_applicabilities = {
            grouping_key['l10n_es_applicability']
            for grouping_key in vals['tax_details']['tax_details']
            if grouping_key['l10n_es_type'] in main_tax_types
        }
        if len(tax_applicabilities) > 1:
            name_map = self.env['account.tax']._l10n_es_edi_verifactu_get_applicability_name_map()
            errors.append(_("We only allow a single Veri*Factu Tax Applicability (Impuesto) per document: %(applicabilities)s.",
                            applicabilities=', '.join([name_map[t] for t in tax_applicabilities])))

        for record_detail in vals['tax_details']['tax_details_per_record'].values():
            main_tax_details = [
                tax_detail for key, tax_detail in record_detail.items()
                if key['l10n_es_type'] in main_tax_types
            ]
            if len(main_tax_details) > 1:
                errors.append(_("We only allow a single \"main\" tax per line."))
                break  # Giving the errors once should be enough

        return errors