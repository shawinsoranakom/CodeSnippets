def action_l10n_vn_edi_update_payment_status(self):
        """ Send a request to update the payment status of the invoice. """

        invoices = self.filtered(lambda i: i.l10n_vn_edi_invoice_state == 'payment_state_to_update')
        if not invoices:
            return

        # == Lock ==
        self.env['res.company']._with_locked_records(invoices)

        for invoice in invoices:
            sinvoice_status = 'unpaid'

            # SInvoice will return a NOT_FOUND_DATA error if the status in Odoo matches the one on their side.
            # Because of that we wouldn't be able to differentiate a real issue (invoice on our side not matching theirs)
            # With simply a status already up to date. So we need to check the status first to see if we need to update.
            invoice_lookup, error_message = invoice._l10n_vn_edi_lookup_invoice()
            if error_message:
                raise UserError(error_message)

            if 'result' in invoice_lookup:
                invoice_data = invoice_lookup['result'][0]
                if invoice_data['status'] == 'Chưa thanh toán':  # Vietnamese for 'unpaid'
                    sinvoice_status = 'unpaid'
                else:
                    sinvoice_status = 'paid'

            params = {
                'supplierTaxCode': invoice.company_id.vat,
                'invoiceNo': invoice.l10n_vn_edi_invoice_number,
                'strIssueDate': invoice._l10n_vn_edi_format_date(invoice.l10n_vn_edi_issue_date),
            }

            if invoice.payment_state in {'in_payment', 'paid'} and sinvoice_status == 'unpaid':
                # Mark the invoice as paid
                endpoint = f'{SINVOICE_API_URL}InvoiceAPI/InvoiceWS/updatePaymentStatus'
                params['templateCode'] = invoice.l10n_vn_edi_invoice_symbol.invoice_template_id.name
            elif invoice.payment_state not in {'in_payment', 'paid'} and sinvoice_status == 'paid':
                # Mark the invoice as not paid
                endpoint = f'{SINVOICE_API_URL}InvoiceAPI/InvoiceWS/cancelPaymentStatus'
            else:
                continue

            access_token, error = self._l10n_vn_edi_get_access_token()
            if error:
                raise UserError(error)

            _request_response, error_message = _l10n_vn_edi_send_request(
                method='POST',
                url=endpoint,
                params=params,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded;',
                },
                cookies={'access_token': access_token},
            )

            if error_message:
                raise UserError(error_message)

            # Revert back to the sent state as the status is up-to-date.
            invoice.l10n_vn_edi_invoice_state = 'sent'

            if self._can_commit():
                self.env.cr.commit()