def pos_order_pay_transaction(self, pos_order_id, access_token=None, **kwargs):
        """ Behaves like payment.PaymentPortal.payment_transaction but for POS online payment.

        :param int pos_order_id: The POS order to pay, as a `pos.order` id
        :param str access_token: The access token used to verify the user
        :param str exit_route: The URL to open to leave the POS online payment flow
        :param dict kwargs: Data from payment module

        :return: The mandatory values for the processing of the transaction
        :rtype: dict
        :raise: AccessError if the provided order or access token is invalid
        :raise: ValidationError if data on the server prevents the payment
        :raise: UserError if data provided by the user is invalid/missing
        """
        pos_order_sudo = self._check_order_access(pos_order_id, access_token)
        self._ensure_session_open(pos_order_sudo)
        exit_route = request.httprequest.args.get('exit_route')
        user_sudo = request.env.user
        if not pos_order_sudo.partner_id:
            user_sudo = pos_order_sudo.company_id._get_public_user()
        logged_in = not user_sudo._is_public()
        partner_sudo = pos_order_sudo.partner_id or self._get_partner_sudo(user_sudo)
        if not partner_sudo:
            return self._redirect_login()

        self._validate_transaction_kwargs(kwargs)
        if kwargs.get('is_validation'):
            raise UserError(
                _("A validation payment cannot be used for a Point of Sale online payment."))

        if 'partner_id' in kwargs and kwargs['partner_id'] != partner_sudo.id:
            raise UserError(
                _("The provided partner_id is different than expected."))
        # Avoid tokenization for the public user.
        kwargs.update({
            'partner_id': partner_sudo.id,
            'partner_phone': partner_sudo.phone,
            'custom_create_values': {
                'pos_order_id': pos_order_sudo.id,
            },
        })
        if not logged_in:
            if kwargs.get('tokenization_requested') or kwargs.get('flow') == 'token':
                raise UserError(
                    _("Tokenization is not available for logged out customers."))
            kwargs['custom_create_values']['tokenize'] = False

        currency_id = pos_order_sudo.currency_id
        if not currency_id.active:
            raise ValidationError(_("The currency is invalid."))
        # Ignore the currency provided by the customer
        kwargs['currency_id'] = currency_id.id

        amount_to_pay = self._get_amount_to_pay(pos_order_sudo)
        if not self._is_valid_amount(amount_to_pay, currency_id):
            raise ValidationError(_("There is nothing to pay for this order."))
        if tools.float_compare(kwargs['amount'], amount_to_pay, precision_rounding=currency_id.rounding) != 0:
            raise ValidationError(
                _("The amount to pay has changed. Please refresh the page."))

        payment_option_id = kwargs.get('payment_method_id') or kwargs.get('token_id')
        if not payment_option_id:
            raise UserError(_("A payment option must be specified."))
        flow = kwargs.get('flow')
        if not (flow and flow in ['redirect', 'direct', 'token']):
            raise UserError(_("The payment should either be direct, with redirection, or made by a token."))
        providers_sudo = self._get_allowed_providers_sudo(pos_order_sudo, partner_sudo.id, amount_to_pay)
        if flow == 'token':
            tokens_sudo = request.env['payment.token']._get_available_tokens(
                providers_sudo.ids, partner_sudo.id)
            if payment_option_id not in tokens_sudo.ids:
                raise UserError(_("The payment token is invalid."))
        else:
            if kwargs.get('provider_id') not in providers_sudo.ids:
                raise UserError(_("The payment provider is invalid."))

        kwargs['reference_prefix'] = None  # Computed with pos_order_id
        kwargs.pop('pos_order_id', None) # _create_transaction kwargs keys must be different than custom_create_values keys

        tx_sudo = self._create_transaction(**kwargs)
        tx_sudo.landing_route = PaymentPortal._get_landing_route(pos_order_sudo.id, access_token, exit_route=exit_route, tx_id=tx_sudo.id)

        return tx_sudo._get_processing_values()