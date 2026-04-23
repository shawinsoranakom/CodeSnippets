def portal_order_page(
        self,
        order_id,
        report_type=None,
        access_token=None,
        message=False,
        download=False,
        payment_amount=None,
        amount_selection=None,
        **kw
    ):
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        payment_amount = self._cast_as_float(payment_amount)
        prepayment_amount = order_sudo._get_prepayment_required_amount()
        if payment_amount and payment_amount < prepayment_amount and order_sudo.state != 'sale':
            raise MissingError(_("The amount is lower than the prepayment amount."))

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(
                model=order_sudo,
                report_type=report_type,
                report_ref='sale.action_report_saleorder',
                download=download,
            )

        # If the route is fetched from the link previewer avoid triggering that quotation is viewed.
        is_link_preview = request.httprequest.headers.get('Odoo-Link-Preview')
        if request.env.user.share and access_token and is_link_preview != 'True':
            # If a public/portal user accesses the order with the access token
            # Log a note on the chatter.
            today = fields.Date.today().isoformat()
            session_obj_date = request.session.get('view_quote_%s' % order_sudo.id)
            if session_obj_date != today:
                # store the date as a string in the session to allow serialization
                request.session['view_quote_%s' % order_sudo.id] = today
                # The "Quotation viewed by customer" log note is an information
                # dedicated to the salesman and shouldn't be translated in the customer/website lgg
                context = {'lang': order_sudo.user_id.partner_id.lang or order_sudo.company_id.partner_id.lang}
                author = order_sudo.partner_id if request.env.user._is_public() else request.env.user.partner_id
                msg = _('Quotation viewed by customer %s', author.name)
                del context
                order_sudo.with_user(SUPERUSER_ID).message_post(
                    body=msg,
                    message_type="notification",
                    subtype_xmlid="sale.mt_order_viewed",
                )

        backend_url = f'/odoo/action-{order_sudo._get_portal_return_action().id}/{order_sudo.id}'
        values = {
            'sale_order': order_sudo,
            'product_documents': order_sudo._get_product_documents(),
            'message': message,
            'report_type': 'html',
            'backend_url': backend_url,
            'res_company': order_sudo.company_id,  # Used to display correct company logo
            'payment_amount': payment_amount,
        }

        # Payment values
        if order_sudo._has_to_be_paid() or (payment_amount and not order_sudo.is_expired):
            values.update(self._get_payment_values(
                order_sudo,
                is_down_payment=self._determine_is_down_payment(
                    order_sudo, amount_selection, payment_amount
                ),
                payment_amount=payment_amount,
            ))
        else:
            values['payment_amount'] = None

        if order_sudo.state in ('draft', 'sent', 'cancel'):
            history_session_key = 'my_quotations_history'
        else:
            history_session_key = 'my_orders_history'

        values = self._get_page_view_values(
            order_sudo, access_token, values, history_session_key, False, **kw)

        return request.render('sale.sale_order_portal_template', values)