def _run_vat_checks(self, country, vat, partner_name='', validation='error'):
        """ OVERRIDE """
        if not country or not vat:
            return vat, False
        if len(vat) == 1:
            if vat == '/' or not validation:
                return vat, False
            if validation == 'setnull':
                return '', False
            if validation == 'error':
                raise ValidationError(_("To explicitly indicate no (valid) VAT, use '/' instead. "))
        vat_prefix, vat_number = self._split_vat(vat)

        if vat_prefix == 'EU' and country not in self.env.ref('base.europe').country_ids:
            # Foreign companies that trade with non-enterprises in the EU
            # may have a VATIN starting with "EU" instead of a country code.
            return vat, False

        do_eu_check = False
        prefixed_country = ''
        eu_prefix_country_group = self.env['res.country.group'].search([('code', '=', 'EU_PREFIX')], limit=1)
        country_code = EU_EXTRA_VAT_CODES_INV.get(vat_prefix, vat_prefix)
        if country_code in eu_prefix_country_group.country_ids.mapped('code'):
            if 'EU_PREFIX' in country.country_group_codes and vat_prefix:
                vat = vat_number
                prefixed_country = vat_prefix
            else:
                do_eu_check = True

        code_to_check = prefixed_country or country.code
        vat = self._format_vat_number(code_to_check, vat)

        if prefixed_country == 'GR':
            prefixed_country = 'EL'

        vat_to_return = prefixed_country + vat

        # The context key 'no_vat_validation' allows you to store/set a VAT number without doing validations.
        # This is for API pushes from external platforms where you have no control over VAT numbers.
        if not validation or self.env.context.get('no_vat_validation'):
            return vat_to_return, code_to_check

        # Avoid validating double prefix like BEBE0477472701
        double_prefix = prefixed_country and vat_to_return.startswith(prefixed_country + prefixed_country)
        if not self._check_vat_number(code_to_check, vat) or double_prefix:
            partner_label = _("partner [%s]", partner_name)
            if do_eu_check:
                try:
                    return self._run_vat_checks(self.env['res.country'].search([('code', '=', country_code)], limit=1), vat_prefix + vat_number, partner_name, validation)
                except ValidationError:
                    msg = self._build_vat_error_message(code_to_check, vat, partner_label)
                    raise ValidationError(msg + "\n\n" + _('If you are trying to input a European number, this is the expected format: ') + _ref_vat[country_code.lower()])
            if validation == 'error':
                msg = self._build_vat_error_message(code_to_check, vat, partner_label)
                raise ValidationError(msg)
            else:
                return '', code_to_check
        return vat_to_return, code_to_check