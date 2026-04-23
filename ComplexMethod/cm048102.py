def _l10n_gr_edi_get_pre_error_dict(self):
        """
        Try to catch all possible errors before sending to myDATA.
        Returns an error dictionary in the format of Actionable Error JSON.
        """
        self.ensure_one()
        errors = {}
        error_action_company = {'action_text': _("View Company"), 'action': self.company_id._get_records_action(name=_("Company"))}
        error_action_partner = {'action_text': _("View Partner"), 'action': self.commercial_partner_id._get_records_action(name=_("Partner"))}
        error_action_gr_settings = {
            'action_text': _("View Settings"),
            'action': {
                'name': _("Settings"),
                'type': 'ir.actions.act_url',
                'target': 'self',
                'url': '/odoo/settings#l10n_gr_edi_aade_settings',
            },
        }

        if self.state != 'posted':
            errors['l10n_gr_edi_move_not_posted'] = {
                'message': _("You can only send to myDATA from a posted invoice."),
            }
        if not self.company_id.l10n_gr_edi_aade_id or not self.company_id.l10n_gr_edi_aade_key:
            errors['l10n_gr_edi_company_no_cred'] = {
                'message': _("You need to set AADE ID and Key in the company settings."),
                **error_action_gr_settings,
            }
        if self.company_id.country_code != 'GR' and (not self.company_id.city or not self.company_id.zip):
            errors['l10n_gr_edi_company_no_zip_street'] = {
                'message': _("Missing city and/or ZIP code on company %s.", self.company_id.name),
                **error_action_company,
            }
        if not self.company_id.vat:
            errors['l10n_gr_edi_company_no_vat'] = {
                'message': _("Missing VAT on company %s.", self.company_id.name),
                **error_action_company,
            }
        if not self.l10n_gr_edi_inv_type:
            errors['l10n_gr_edi_no_inv_type'] = {
                'message': _("Missing myDATA Invoice Type."),
            }
        if not self.commercial_partner_id:
            errors['l10n_gr_edi_no_partner'] = {
                'message': _("Partner must be filled to be able to send to myDATA."),
            }
        if self.commercial_partner_id:
            if not self.commercial_partner_id.vat:
                errors['l10n_gr_edi_partner_no_vat'] = {
                    'message': _("Missing VAT on partner %s.", self.commercial_partner_id.name),
                    **error_action_partner,
                }
            if ((self.commercial_partner_id.country_code != 'GR' or self.l10n_gr_edi_inv_type in TYPES_WITH_MANDATORY_COUNTERPART) and
                    (not self.commercial_partner_id.zip or not self.commercial_partner_id.city)):
                errors['l10n_gr_edi_partner_no_zip_street'] = {
                    'message': _("Missing city and/or ZIP code on partner %s.", self.commercial_partner_id.name),
                    **error_action_partner,
                }

        move_disallow_classification = self.is_purchase_document(include_receipts=True) and self.l10n_gr_edi_inv_type in TYPES_WITH_FORBIDDEN_CLASSIFICATION

        for line_no, line in enumerate(self.invoice_line_ids, start=1):
            if line.display_type in ('line_section', 'line_subsection', 'line_note'):
                continue
            if move_disallow_classification and line.l10n_gr_edi_cls_category:
                errors[f'l10n_gr_edi_{line_no}_forbidden_classification'] = {
                    'message': _('myDATA classification is not allowed on line %s.', line_no),
                }
            if not line.l10n_gr_edi_cls_category and line.l10n_gr_edi_available_cls_category and not move_disallow_classification:
                errors[f'l10n_gr_edi_line_{line_no}_missing_cls_category'] = {
                    'message': _('Missing myDATA classification category on line %s.', line_no),
                }
            if not line.l10n_gr_edi_cls_type \
                    and line.l10n_gr_edi_available_cls_type \
                    and (line.move_id.l10n_gr_edi_inv_type, line.l10n_gr_edi_cls_category) \
                    not in COMBINATIONS_WITH_POSSIBLE_EMPTY_TYPE:
                errors[f'l10n_gr_edi_line_{line_no}_missing_cls_type'] = {
                    'message': _('Missing myDATA classification type on line %s.', line_no),
                }
            taxes = line.tax_ids.flatten_taxes_hierarchy()
            if len(taxes) > 1:
                errors[f'l10n_gr_edi_line_{line_no}_multi_tax'] = {
                    'message': _('myDATA does not support multiple taxes on line %s.', line_no),
                }
            if not taxes and self.l10n_gr_edi_inv_type not in TYPES_WITH_VAT_CATEGORY_8:
                errors[f'l10n_gr_edi_line_{line_no}_missing_tax'] = {
                    'message': _('Missing tax on line %s.', line_no),
                }
            if len(taxes) == 1 and taxes.amount == 0 and not line.l10n_gr_edi_tax_exemption_category:
                errors[f'l10n_gr_edi_line_{line_no}_missing_tax_exempt'] = {
                    'message': _('Missing myDATA Tax Exemption Category for line %s.', line_no),
                }
            if len(taxes) == 1 and taxes.amount not in VALID_TAX_AMOUNTS:
                errors[f'l10n_gr_edi_line_{line_no}_invalid_tax_amount'] = {
                    'message': _('Invalid tax amount for line %(line_no)s. The valid values are %(valid_values)s.',
                                 line_no=line_no,
                                 valid_values=', '.join(str(tax) for tax in VALID_TAX_AMOUNTS)),
                }
        return errors