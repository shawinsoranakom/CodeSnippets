def stripe_webhook(self):
        """Process the payment data sent by Stripe to the webhook.

        :return: An empty string to acknowledge the notification.
        :rtype: str
        """
        event = request.get_json_data()
        _logger.info("Notification received from Stripe with data:\n%s", pprint.pformat(event))
        try:
            if event['type'] in const.HANDLED_WEBHOOK_EVENTS:
                stripe_object = event['data']['object']  # {Payment,Setup}Intent, Charge, or Refund.

                # Check the integrity of the event.
                data = {
                    'reference': stripe_object.get('description'),
                    'event_type': event['type'],
                    'object_id': stripe_object['id'],
                }
                tx_sudo = request.env['payment.transaction'].sudo()._search_by_reference(
                    'stripe', data
                )

                if not tx_sudo:
                    return request.make_json_response('')

                self._verify_signature(tx_sudo)

                if event['type'].startswith('payment_intent'):  # Payment operation.
                    if tx_sudo.tokenize:
                        payment_method = tx_sudo._send_api_request(
                            'GET', f'payment_methods/{stripe_object["payment_method"]}'
                        )
                        stripe_object['payment_method'] = payment_method
                    self._include_payment_intent_in_payment_data(stripe_object, data)
                elif event['type'].startswith('setup_intent'):  # Validation operation.
                    # Fetch the missing PaymentMethod object.
                    payment_method = tx_sudo._send_api_request(
                        'GET', f'payment_methods/{stripe_object["payment_method"]}'
                    )
                    stripe_object['payment_method'] = payment_method
                    self._include_setup_intent_in_payment_data(stripe_object, data)
                elif event['type'] == 'charge.refunded':  # Refund operation (refund creation).
                    if not stripe_object['captured']:  # The charge was authorized and then voided
                        return request.make_json_response('')  # Don't process void-related events

                    refunds = stripe_object['refunds']['data']

                    # The refunds linked to this charge are paginated, fetch the remaining refunds.
                    has_more = stripe_object['refunds']['has_more']
                    while has_more:
                        payload = {
                            'charge': stripe_object['id'],
                            'starting_after': refunds[-1]['id'],
                            'limit': 100,
                        }
                        additional_refunds = tx_sudo._send_api_request(
                            'GET', 'refunds', data=payload
                        )
                        refunds += additional_refunds['data']
                        has_more = additional_refunds['has_more']

                    # Process the refunds for which a refund transaction has not been created yet.
                    processed_refund_ids = tx_sudo.child_transaction_ids.filtered(
                        lambda tx: tx.operation == 'refund'
                    ).mapped('provider_reference')
                    for refund in filter(lambda r: r['id'] not in processed_refund_ids, refunds):
                        refund_tx_sudo = self._create_refund_tx_from_refund(tx_sudo, refund)
                        self._include_refund_in_payment_data(refund, data)
                        refund_tx_sudo._process('stripe', data)
                    # Don't process the payment data for the source transaction.
                    return request.make_json_response('')
                elif event['type'] == 'charge.refund.updated':  # Refund operation (with update).
                    # A refund was updated by Stripe after it was already processed (possibly to
                    # cancel it). This can happen when the customer's payment method can no longer
                    # be topped up (card expired, account closed...). The `tx_sudo` record is the
                    # refund transaction to update.
                    self._include_refund_in_payment_data(stripe_object, data)

                # Process the payment data crafted with Stripe API objects
                tx_sudo._process('stripe', data)
        except ValidationError:  # Acknowledge the notification to avoid getting spammed
            _logger.exception("Unable to process the payment data; skipping to acknowledge")
        return request.make_json_response('')