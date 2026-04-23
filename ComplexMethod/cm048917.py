def donation_transaction(self, amount, currency_id, partner_id, access_token, minimum_amount=0, **kwargs):
        if float(amount) < float(minimum_amount):
            raise ValidationError(_('Donation amount must be at least %.2f.', float(minimum_amount)))
        use_public_partner = request.env.user._is_public() or not partner_id
        if use_public_partner:
            details = kwargs['partner_details']
            if not details.get('name'):
                raise ValidationError(_('Name is required.'))
            if not details.get('email'):
                raise ValidationError(_('Email is required.'))
            if not details.get('country_id'):
                raise ValidationError(_('Country is required.'))
            partner_id = request.website.user_id.partner_id.id
            del kwargs['partner_details']
        else:
            partner_id = request.env.user.partner_id.id

        self._validate_transaction_kwargs(kwargs, additional_allowed_keys=(
            'donation_comment', 'donation_recipient_email', 'partner_details', 'reference_prefix'
        ))
        if use_public_partner:
            kwargs['custom_create_values'] = {'tokenize': False}
        tx_sudo = self._create_transaction(
            amount=amount, currency_id=currency_id, partner_id=partner_id, **kwargs
        )
        tx_sudo.is_donation = True
        if use_public_partner:
            tx_sudo.update({
                'partner_name': details['name'],
                'partner_email': details['email'],
                'partner_country_id': int(details['country_id']),
            })
        elif not tx_sudo.partner_country_id:
            tx_sudo.partner_country_id = int(kwargs['partner_details']['country_id'])
        # the user can change the donation amount on the payment page,
        # therefor we need to recompute the access_token
        access_token = payment_utils.generate_access_token(
            tx_sudo.partner_id.id, tx_sudo.amount, tx_sudo.currency_id.id
        )
        self._update_landing_route(tx_sudo, access_token)

        # Send a notification to warn that a donation has been made
        recipient_email = kwargs['donation_recipient_email']
        comment = kwargs['donation_comment']
        tx_sudo._send_donation_email(True, comment, recipient_email)

        return tx_sudo._get_processing_values()