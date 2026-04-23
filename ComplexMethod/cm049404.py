def registration_confirm(self, event, **post):
        res = super().registration_confirm(event, **post)

        registrations = self._process_attendees_form(event, post)
        order_sudo = request.cart
        if not any(line.event_ticket_id for line in order_sudo.order_line):
            # order does not contain any tickets, meaning we are confirming a free event
            return res

        # we have at least one registration linked to a ticket -> sale mode activate
        if any(info['event_ticket_id'] for info in registrations):
            if order_sudo.amount_total:
                if order_sudo._is_anonymous_cart():
                    booked_by_partner, feedback_dict = CustomerPortal()._create_or_update_address(
                        request.env['res.partner'].sudo(),
                        order_sudo=order_sudo,
                        verify_address_values=False,
                        **registrations[0]
                    )
                    if not feedback_dict.get('invalid_fields'):
                        order_sudo._update_address(booked_by_partner.id, ['partner_id'])
                request.session['sale_last_order_id'] = order_sudo.id
                return request.redirect("/shop/checkout?try_skip_step=true")
            else:
                # Free order -> auto confirmation without checkout
                order_sudo.action_confirm()  # tde notsure: email sending ?
                request.website.sale_reset()
                request.session['sale_last_order_id'] = order_sudo.id
                return request.redirect("/shop/confirmation")

        return res