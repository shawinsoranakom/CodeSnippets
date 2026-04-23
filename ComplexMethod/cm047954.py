def _l10n_hu_edi_recover_transactions(self, connection):
        """ Recover transactions that are in force but for some reason are not matched to the company's
        invoices, and update the invoice state correspondingly.

        This can happen, for example, if the invoice sending timed out: in that case, we don't have a
        transaction ID for the invoice. It can also happen if for some reason the transaction ID was
        overwritten by a new request, but the new request fails with a 'duplicate invoice' error.

        To do this, we request a list of all transactions made since l10n_hu_edi_last_transaction_recovery,
        and then we query the last 10 transactions whose transaction IDs are unknown by Odoo. We try to
        match them to invoices in Odoo, and if successful, update the invoice state.
        """

        for company in self:
            # We use the l10n_hu_edi_last_transaction_recovery time only in production mode
            # to indicate which transactions to request.
            # In test mode (where we expect far fewer invoices), we just take the last 24 hours.
            recovery_end_time = fields.Datetime.now()
            if company.l10n_hu_edi_server_mode == 'production':
                recovery_start_time = company.l10n_hu_edi_last_transaction_recovery
            else:
                recovery_start_time = recovery_end_time - timedelta(hours=24)

            # Old invoices are already up-to-date - no need to re-check them.
            invoices_to_check = self.env['account.move'].search([
                ('company_id', '=', company.id),
                ('l10n_hu_edi_send_time', '>=', recovery_start_time),
                ('l10n_hu_edi_state', '!=', False),
            ])
            # Step 1: Request a list of all transactions made during the specified time interval.
            page = 1
            available_pages = 1
            transactions = []
            while page <= available_pages:
                try:
                    transaction_list = connection.do_query_transaction_list(
                        company.sudo()._l10n_hu_edi_get_credentials_dict(),
                        recovery_start_time,
                        recovery_end_time,
                        page,
                    )
                except L10nHuEdiConnectionError as e:
                    return {
                        'error_title': _('Error listing transactions while attempting transaction recovery.'),
                        'errors': e.errors,
                    }

                available_pages = transaction_list['available_pages']
                transactions += transaction_list['transactions']
                page += 1

            # Step 2: Query unknown transactions in reverse order (latest first) and update invoice states accordingly.
            # If there are too many, we should only query the last 10, to avoid pointlessly making huge numbers of requests.
            transactions_to_query = (
                t for t in reversed(transactions)
                if t['username'] == company.sudo().l10n_hu_edi_username
                    and t['source'] == 'MGM'
                    and t['transaction_code'] not in invoices_to_check.mapped('l10n_hu_edi_transaction_code')
            )

            for transaction in islice(transactions_to_query, 10):
                try:
                    results = connection.do_query_transaction_status(
                        company.sudo()._l10n_hu_edi_get_credentials_dict(),
                        transaction['transaction_code'],
                        return_original_request=True,
                    )
                except L10nHuEdiConnectionError as e:
                    return {
                        'error_title': _('Error querying transaction while attempting transaction recovery.'),
                        'errors': e.errors,
                    }

                for processing_result in results['processing_results']:
                    invoice_name = processing_result['original_xml'].findtext('data:invoiceNumber', namespaces=XML_NAMESPACES)
                    canonicalized_attachment = etree.canonicalize(processing_result['original_file'])
                    annulment_invoice_name = processing_result['original_xml'].findtext('data:annulmentReference', namespaces=XML_NAMESPACES)

                    matched_invoice = invoices_to_check.filtered(
                        lambda m: (
                            # 1. Match invoice if the entire XML matches.
                            # For performance, we first check the invoice name before trying to match the whole XML.
                            (
                                m.name == invoice_name
                                and etree.canonicalize(base64.b64decode(m.l10n_hu_edi_attachment).decode())
                                    == canonicalized_attachment
                            )
                            or m.name == annulment_invoice_name
                        ) and (
                            # 2. We update the invoice state only if:
                            # - the invoice doesn't have a transaction code, or
                            # - it currently has a duplicate error, or
                            # - the current transaction is more recent than the latest transaction on the invoice
                            #   and is not a duplicate error (this avoid overwriting the state with a previous, obsolete one).
                            not m.l10n_hu_edi_transaction_code
                            or any(
                                'INVOICE_NUMBER_NOT_UNIQUE' in error or 'ANNULMENT_IN_PROGRESS' in error
                                for error in m.l10n_hu_edi_messages['errors']
                            )
                            or (
                                transaction['send_time'] >= m.l10n_hu_edi_send_time
                                and not (
                                    processing_result['technical_validation_messages']
                                    or any(
                                        message['validation_error_code'] in ['INVOICE_NUMBER_NOT_UNIQUE', 'ANNULMENT_IN_PROGRESS']
                                        for message in processing_result['business_validation_messages']
                                    )
                                )
                            )
                        )
                    )

                    if matched_invoice:
                        # Set the correct transaction code on the matched invoice
                        matched_invoice.l10n_hu_edi_transaction_code = transaction['transaction_code']
                        matched_invoice._l10n_hu_edi_process_query_transaction_result(processing_result, results['annulment_status'])

            # The server might still be processing transactions from the last 6 minutes,
            # so we should keep open the possibility of re-querying them.
            recovery_close_time = recovery_end_time - timedelta(minutes=6)
            if company.l10n_hu_edi_server_mode == 'production':
                company.l10n_hu_edi_last_transaction_recovery = recovery_close_time

            # Any invoices still in a 'timeout' state that are more than 6 minutes old and could not be matched should be considered not received.
            invoices_to_check.filtered(
                lambda m: m.l10n_hu_edi_state == 'send_timeout' and m.l10n_hu_edi_send_time < recovery_close_time
            ).write({
                'l10n_hu_invoice_chain_index': 0,
                'l10n_hu_edi_state': 'rejected',
            })

            invoices_to_check.filtered(
                lambda m: m.l10n_hu_edi_state == 'cancel_timeout' and m.l10n_hu_edi_send_time < recovery_close_time
            ).write({
                'l10n_hu_edi_state': 'confirmed_warning',
            })