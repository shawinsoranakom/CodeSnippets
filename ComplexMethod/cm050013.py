def _search_by_reference(self, provider_code, payment_data):
        """Override of `payment` to search the transaction  with a specific logic for Adyen."""
        if provider_code != 'adyen':
            return super()._search_by_reference(provider_code, payment_data)

        tx = self
        reference = payment_data.get('merchantReference')
        if not reference:
            _logger.warning("Received data with missing reference.")
            return tx

        event_code = payment_data.get('eventCode', 'AUTHORISATION')  # Fallback on auth if S2S.
        provider_reference = payment_data.get('pspReference')
        source_reference = payment_data.get('originalReference')
        if event_code == 'AUTHORISATION':
            tx = self.search([('reference', '=', reference), ('provider_code', '=', 'adyen')])
        elif event_code in ['CANCELLATION', 'CAPTURE', 'CAPTURE_FAILED']:
            # The capture/void may be initiated from Adyen, so we can't trust the reference.
            # We find the transaction based on the original provider reference since Adyen will have
            # two different references: one for the original transaction and one for the capture or
            # void. We keep the second one only for child transactions.
            source_tx = self.search(
                [('provider_reference', '=', source_reference), ('provider_code', '=', 'adyen')]
            )
            tx = self.search(
                [('provider_reference', '=', provider_reference), ('provider_code', '=', 'adyen')]
            )
            if source_tx:
                payment_data_amount = payment_data.get('amount', {}).get('value')
                converted_notification_amount = payment_utils.to_major_currency_units(
                    payment_data_amount,
                    source_tx.currency_id,
                    arbitrary_decimal_number=const.CURRENCY_DECIMALS.get(self.currency_id.name),
                )
                if tx and tx.amount != converted_notification_amount:
                    # If the void was requested expecting a certain amount but, in the meantime,
                    # others captures that Odoo was unaware of were done, the amount voided will
                    # be different from the amount of the existing transaction.
                    tx._set_error(_(
                        "The amount processed by Adyen for the transaction %s is different than"
                        " the one requested. Another transaction is created with the correct"
                        " amount.", tx.reference
                    ))
                    tx = self.env['payment.transaction']
                if not tx:  # capture/void initiated from Adyen or with a wrong amount.
                    # Manually create a child transaction with a new reference. The reference of
                    # the child transaction was personalized from Adyen and could be identical
                    # to that of an existing transaction.
                    tx = self._adyen_create_child_tx(source_tx, payment_data)
            else:  # The capture/void was initiated for an unknown source transaction
                pass  # Don't do anything with the capture/void notification
        else:  # 'REFUND'
            # The refund may be initiated from Adyen, so we can't trust the reference, which could
            # be identical to another existing transaction. We find the transaction based on the
            # provider reference.
            tx = self.search(
                [('provider_reference', '=', provider_reference), ('provider_code', '=', 'adyen')]
            )
            if not tx:  # The refund was initiated from Adyen
                # Find the source transaction based on the original reference
                source_tx = self.search(
                    [('provider_reference', '=', source_reference), ('provider_code', '=', 'adyen')]
                )
                if source_tx:
                    # Manually create a refund transaction with a new reference. The reference of
                    # the refund transaction was personalized from Adyen and could be identical to
                    # that of an existing transaction.
                    tx = self._adyen_create_child_tx(source_tx, payment_data, is_refund=True)
                else:  # The refund was initiated for an unknown source transaction
                    pass  # Don't do anything with the refund notification
        if not tx:
            _logger.warning("No transaction found matching reference %s.", reference)
        return tx