def _l10n_it_edi_export_check(self, checks=None):
        checks = checks or ['partner_vat_codice_fiscale_missing', 'partner_address_missing']
        fields_to_check = {
            'partner_vat_missing': {
                'fields': [('vat',)],
                'message': _("Partner(s) should have a VAT number."),
            },
            'partner_vat_codice_fiscale_missing': {
                'fields': [('vat', 'l10n_it_codice_fiscale')],
                'message': _("Partner(s) should have a VAT number or Codice Fiscale."),
            },
            'partner_country_missing': {
                'fields': [('country_id',)],
                'message': _("Partner(s) should have a Country when used for simplified invoices."),
            },
            'partner_address_missing': {
                'fields': [('street', 'street2'), ('zip',), ('city',), ('country_id',)],
                'message': _("Partner(s) should have a complete address, verify their Street, City, Zipcode and Country."),
            },
        }
        selected_checks = {k: v for k, v in fields_to_check.items() if k in checks}
        single_views = [(False, 'form')]
        list_view = (self.env.ref('l10n_it_edi.res_partner_tree_l10n_it', raise_if_not_found=False))
        multi_views = [(list_view.id if list_view else False, 'list'), (False, 'form')]
        errors = {}
        for key, check in selected_checks.items():
            for fields_tuple in check['fields']:
                if invalid_records := self.filtered(lambda record: not any(record[field] for field in fields_tuple)):
                    views = single_views if len(invalid_records) == 1 else multi_views
                    errors[f"l10n_it_edi_{key}"] = {
                        'message': check['message'],
                        'action_text': _("View Partner(s)"),
                        'action': invalid_records._get_records_action(name=_("Check Partner(s)"), views=views),
                    }
        return errors