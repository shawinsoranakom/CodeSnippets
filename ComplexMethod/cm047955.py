def _call_web_service_before_invoice_pdf_render(self, invoices_data):
        # EXTENDS 'account'
        super()._call_web_service_before_invoice_pdf_render(invoices_data)

        invoices_hu = self.env['account.move'].browse([
            invoice.id
            for invoice, invoice_data in invoices_data.items()
            if 'hu_nav_30' in invoice_data['extra_edis']
               and 'upload' in invoice._l10n_hu_edi_get_valid_actions()
        ])

        if not invoices_hu:
            return

        # Pre-emptively acquire write lock on all invoices to be processed
        # Otherwise, we will get a serialization error later
        # (bad, because Odoo will try to retry the entire request, leading to duplicate sending to NAV)
        invoices_hu._l10n_hu_edi_acquire_lock()

        # STEP 1: Generate and send the invoice XMLs.
        invoices_to_upload = invoices_hu.filtered(lambda m: 'upload' in m._l10n_hu_edi_get_valid_actions())

        # If we need to re-generate the PDF, break the link between the existing attachment and the 'invoice_pdf_report_file' field.
        # The existing PDF will remain linked to the invoice, but no longer as primary attachment.
        invoices_to_upload.invoice_pdf_report_id.write({'res_field': False})
        invoices_to_upload.invalidate_recordset(fnames=['invoice_pdf_report_id', 'invoice_pdf_report_file'])

        with L10nHuEdiConnection(self.env) as connection:
            invoices_to_upload._l10n_hu_edi_upload(connection)
            if self._can_commit():
                self.env.cr.commit()

            if any(m.l10n_hu_edi_state == 'sent' for m in invoices_hu):
                # If any invoices were just sent, wait so that NAV has enough time to process them
                time.sleep(2)

            # STEP 2: Query status
            invoices_hu.filtered(lambda m: 'query_status' in m._l10n_hu_edi_get_valid_actions())._l10n_hu_edi_query_status(connection)

        # STEP 3: Schedule update status of pending invoices in 10 minutes.
        if any(m.l10n_hu_edi_state not in [False, 'confirmed', 'confirmed_warning', 'rejected'] for m in invoices_hu):
            self.env.ref('l10n_hu_edi.ir_cron_update_status')._trigger(at=fields.Datetime.now() + timedelta(minutes=10))

        # STEP 4: Error / success handling.
        for invoice in invoices_hu:
            # Log outcome in chatter
            formatted_message = self._format_error_html(invoice.l10n_hu_edi_messages)
            invoice.message_post(body=formatted_message)

            # Update invoice_data with errors
            blocking_level = invoice.l10n_hu_edi_messages.get('blocking_level')
            if blocking_level == 'error':
                invoices_data[invoice]['error'] = invoice.l10n_hu_edi_messages

        if self._can_commit():
            self.env.cr.commit()