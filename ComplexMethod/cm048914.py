def _send_refund_request(self):
        """Override of `payment` to send a refund request to Authorize."""
        if self.provider_code != 'authorize':
            return super()._send_refund_request()

        authorize_api = AuthorizeAPI(self.provider_id)
        tx_details = authorize_api.get_transaction_details(
            self.source_transaction_id.provider_reference
        )
        if 'err_code' in tx_details:  # Could not retrieve the transaction details.
            self._set_error(_(
                "Could not retrieve the transaction details. (error code: %(error_code)s; error_details: %(error_message)s)",
                error_code=tx_details['err_code'], error_message=tx_details.get('err_msg'),
            ))
            return

        tx_status = tx_details.get('transaction', {}).get('transactionStatus')
        if tx_status in const.TRANSACTION_STATUS_MAPPING['voided']:
            # The payment has been voided from Authorize.net side before we could refund it.
            self._set_canceled(extra_allowed_states=('done',))
        elif tx_status in const.TRANSACTION_STATUS_MAPPING['refunded']:
            # The payment has been refunded from Authorize.net side before we could refund it. We
            # create a refund tx on Odoo to reflect the move of the funds.
            self._set_done()
            # Immediately post-process the transaction as the post-processing will not be
            # triggered by a customer browsing the transaction from the portal.
            self.env.ref('payment.cron_post_process_payment_tx')._trigger()
        elif any(tx_status in const.TRANSACTION_STATUS_MAPPING[k] for k in ('authorized', 'captured')):
            if tx_status in const.TRANSACTION_STATUS_MAPPING['authorized']:
                # The payment has not been settled on Authorize.net yet. It must be voided rather
                # than refunded. Since the funds have not moved yet, we don't create a refund tx.
                res_content = authorize_api.void(self.source_transaction_id.provider_reference)
            else:
                # The payment has been settled on Authorize.net side. We can refund it.
                rounded_amount = round(self.amount, self.currency_id.decimal_places)
                res_content = authorize_api.refund(
                    self.provider_reference, rounded_amount, tx_details
                )
            _logger.info(
                "refund request response for transaction %s:\n%s",
                self.reference, pprint.pformat(res_content)
            )
            data = {'reference': self.reference, 'response': res_content}
            self._process('authorize', data)
        else:
            err_msg = _(
                "The transaction is not in a status to be refunded."
                " (status: %(status)s, details: %(message)s)",
                status=tx_status, message=tx_details.get('messages', {}).get('message'),
            )
            _logger.warning(err_msg)
            self._set_error(err_msg)