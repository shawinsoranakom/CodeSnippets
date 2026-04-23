def invoice_request_screen(self, **kwargs):
        errors = {}
        form_values = {}
        if request.httprequest.method == 'POST':
            for field in ['pos_reference', 'date_order', 'ticket_code']:
                if not kwargs.get(field):
                    errors[field] = " "
                else:
                    form_values[field] = kwargs.get(field)

            if errors:
                errors['generic'] = _("Please fill all the required fields.")
            elif len(form_values['pos_reference']) < 12:
                errors['pos_reference'] = _("The Ticket Number should be at least 12 characters long.")
            else:
                date_order = datetime(*[int(i) for i in form_values['date_order'].split('-')])
                order = request.env['pos.order'].sudo().search([
                    ('pos_reference', '=like', '%' + form_values['pos_reference'].strip().replace('%', r'\%').replace('_', r'\_')),
                    ('date_order', '>=', date_order - timedelta(days=1)),
                    ('date_order', '<', date_order + timedelta(days=2)),
                    ('ticket_code', '=', form_values['ticket_code']),
                ], limit=1)
                if order:
                    return request.redirect('/pos/ticket/validate?access_token=%s' % (order.access_token))
                else:
                    errors['generic'] = _("No sale order found.")

        elif request.httprequest.method == 'GET':
            if kwargs.get('order_uuid'):
                order = self.env['pos.order'].sudo().search([('uuid', '=', kwargs['order_uuid'])], limit=1)
                if order:
                    return request.redirect('/pos/ticket/validate?access_token=%s' % (order.access_token))

        return request.render("point_of_sale.ticket_request_with_code", {
            'errors': errors,
            'banner_error': " ".join(errors.values()),
            'form_values': form_values,
        })