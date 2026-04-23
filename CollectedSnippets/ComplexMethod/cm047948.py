def l10n_hu_edi_button_update_status(self, from_cron=False):
        """ Attempt to update the status of the invoices in `self` """
        invoices_to_query = self.filtered(lambda m: 'query_status' in m._l10n_hu_edi_get_valid_actions())

        with L10nHuEdiConnection(self.env) as connection:
            # Call `query_status` on the invoices.
            invoices_to_query._l10n_hu_edi_query_status(connection)

            # Attempt to recover missing transactions, if any invoice is missing a transaction code
            # or has a duplicate error.
            recover_transactions_error = False
            if any(
                not m.l10n_hu_edi_transaction_code
                or any(
                    'INVOICE_NUMBER_NOT_UNIQUE' in error or 'ANNULMENT_IN_PROGRESS' in error
                    for error in m.l10n_hu_edi_messages['errors']
                )
                for m in self
            ):
                recover_transactions_error = self.company_id._l10n_hu_edi_recover_transactions(connection)

        # Error handling.
        for invoice in invoices_to_query:
            # Log invoice status in chatter.
            formatted_message = self.env['account.move.send']._format_error_html(invoice.l10n_hu_edi_messages)
            invoice.message_post(body=formatted_message)

        if self.env['account.move.send']._can_commit():
            self.env.cr.commit()

        # If blocking errors, raise UserError, or log if we are in a cron.
        for invoice in invoices_to_query:
            if invoice.l10n_hu_edi_messages.get('blocking_level') == 'error' or recover_transactions_error:
                if invoice.l10n_hu_edi_messages.get('blocking_level') == 'error':
                    error_text = self.env['account.move.send']._format_error_text(invoice.l10n_hu_edi_messages)
                else:
                    error_text = self.env['account.move.send']._format_error_text(recover_transactions_error)
                if not from_cron:
                    raise UserError(error_text)
                else:
                    _logger.error(error_text)