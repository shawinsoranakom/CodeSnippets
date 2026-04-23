def blacklist_page(self, mailing_id, trace_code, **post):
        """ Main entry point for unsubscribe links. Verify trace code (should
        match mailing and trace), then check number can be sanitized. """
        check_res = self._check_trace(mailing_id, trace_code)
        found_traces = check_res.get('trace')
        if not found_traces:
            return request.redirect('/odoo')

        valid_trace = request.env['mailing.trace'].sudo()
        sanitized_number = False
        sms_number = post.get('sms_number', '').strip()
        if sms_number:
            country = request.env['res.country'].sudo()
            if country_code := request.geoip.country_code:
                country = request.env['res.country'].search([('code', '=', country_code)], limit=1)
            if not country:
                country = request.env.company.country_id
            try:
                # Sanitize the phone number
                sanitized_number = phone_validation.phone_format(
                    sms_number,
                    country.code,
                    country.phone_code,
                    force_format='E164',
                    raise_exception=True,
                )
            except Exception:  # noqa: BLE001
                sanitized_number = False

            if sanitized_number:
                valid_trace = found_traces.filtered(lambda t: t.sms_number == sanitized_number)

        # trace found -> number valid, code matching
        if valid_trace:
            return request.redirect(
                f'/sms/{mailing_id}/unsubscribe/{trace_code}?{werkzeug.urls.url_encode({"sms_number": sanitized_number})}'
            )

        # otherwise: generate error message, loop on same page
        unsubscribe_error = False
        if sms_number and not sanitized_number:
            unsubscribe_error = _('Oops! The phone number seems to be incorrect. Please make sure to include the country code.')
        if sanitized_number and not valid_trace:
            unsubscribe_error = _('Oops! Number not found')
        return request.render('mass_mailing_sms.blacklist_main', {
            'mailing_id': mailing_id,
            'sms_number': sms_number,
            'trace_code': trace_code,
            'unsubscribe_error': unsubscribe_error,
        })