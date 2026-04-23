def _generate_and_send_invoices(self, moves, from_cron=False, allow_raising=True, allow_fallback_pdf=False, **custom_settings):
        """ Generate and send the moves given custom_settings if provided, else their default configuration set on related partner/company.
        :param moves: account.move to process
        :param from_cron: whether the processing comes from a cron.
        :param allow_raising: whether the process can raise errors, or should log them on the move's chatter.
        :param allow_fallback_pdf:  In case of error when generating the documents for invoices, generate a proforma PDF report instead.
        :param custom_settings: settings to apply instead of related partner's defaults settings.
        """
        self._check_sending_data(moves, **custom_settings)
        moves_data = {
            move.sudo(): {
                **self._get_default_sending_settings(move, from_cron=from_cron, **custom_settings),
            }
            for move in moves
        }

        # Generate all invoice documents (PDF and electronic documents if relevant).
        self._generate_invoice_documents(moves_data, allow_fallback_pdf=allow_fallback_pdf)

        # Manage errors.
        errors = {move: move_data for move, move_data in moves_data.items() if move_data.get('error')}
        if errors:
            self._hook_if_errors(errors, allow_raising=not from_cron and not allow_fallback_pdf and allow_raising)

        # Fallback in case of error.
        errors = {move: move_data for move, move_data in moves_data.items() if move_data.get('error')}
        if allow_fallback_pdf and errors:
            self._generate_invoice_fallback_documents(errors)

        # Successfully generated a PDF - Process sending.
        success = {move: move_data for move, move_data in moves_data.items() if not move_data.get('error')}
        if success:
            self._hook_if_success(success, from_cron=from_cron)

        # Update sending data of moves
        for move, move_data in moves_data.items():
            # We keep the sending_data, so it will be retried
            if from_cron and move_data.get('error', {}).get('retry'):
                continue
            move.sending_data = False

        # Return generated attachments.
        attachments = self.env['ir.attachment']
        for move, move_data in success.items():
            attachments += self._get_invoice_extra_attachments(move) or move_data['proforma_pdf_attachment']

        return attachments