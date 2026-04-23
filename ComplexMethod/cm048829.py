def l10n_tw_invoicing_info_post(self, **kw):
        order_sudo = request.cart
        errors = {}
        default_vals = {
            'love_code': kw.get('l10n_tw_edi_love_code'),
            'carrier_type': kw.get('l10n_tw_edi_carrier_type'),
            'carrier_number': kw.get('l10n_tw_edi_carrier_number'),
            'carrier_number_2': kw.get('l10n_tw_edi_carrier_number_2'),
            'is_donate': kw.get('l10n_tw_edi_is_donate'),
        }
        if kw.get('l10n_tw_edi_is_donate') != 'on':
            if kw.get('l10n_tw_edi_carrier_type') == '2' and not kw.get('l10n_tw_edi_carrier_number'):
                errors['carrier_number'] = request.env._('Please enter the storage code')
            if kw.get('l10n_tw_edi_carrier_type') == '3' \
                    and not self._is_valid_mobile_barcode(kw.get('l10n_tw_edi_carrier_number'), order_sudo):
                errors['carrier_number'] = request.env._('Mobile Barcode is invalid')
            if kw.get('l10n_tw_edi_carrier_type') in ['4', '5'] and (not kw.get('l10n_tw_edi_carrier_number') or not kw.get('l10n_tw_edi_carrier_number_2')):
                errors['carrier_number'] = request.env._('Please enter the storage code and storage code 2')
        elif kw.get('l10n_tw_edi_is_donate') == 'on' and not self._is_valid_love_code(kw.get('l10n_tw_edi_love_code'), order_sudo):
            errors['love_code'] = request.env._('Donation Code is invalid')

        vals_to_write = {
            'l10n_tw_edi_is_print': False,
            'l10n_tw_edi_love_code': False,
            'l10n_tw_edi_carrier_type': False,
            'l10n_tw_edi_carrier_number': False,
            'l10n_tw_edi_carrier_number_2': False,
        }

        is_donate = default_vals.get('is_donate') == 'on'

        if is_donate and 'love_code' not in errors:
            vals_to_write['l10n_tw_edi_love_code'] = default_vals.get('love_code')

        if not is_donate and 'carrier_number' not in errors:
            carrier_type = default_vals.get('carrier_type')

            if carrier_type != '0':
                vals_to_write['l10n_tw_edi_carrier_type'] = carrier_type

            if carrier_type in ['2', '3', '4', '5']:
                vals_to_write['l10n_tw_edi_carrier_number'] = default_vals.get('carrier_number')

            if carrier_type in ['4', '5']:
                vals_to_write['l10n_tw_edi_carrier_number_2'] = default_vals.get('carrier_number_2')

        order_sudo.write(vals_to_write)

        if not errors:
            request.httprequest.path = '/shop/l10n_tw_invoicing_info'
            return request.redirect(
                request.website._get_checkout_step_values()['next_website_checkout_step_href']
            )

        values = self._get_render_context(order_sudo, default_vals, errors)
        values.update(request.website._get_checkout_step_values())
        return request.render('l10n_tw_edi_ecpay_website_sale.l10n_tw_edi_invoicing_info', values)