def _call_web_service_after_invoice_pdf_render(self, invoices_data):
        # EXTENDS 'account'
        super()._call_web_service_after_invoice_pdf_render(invoices_data)

        params = {'documents': []}
        invoices_data_peppol = {}
        to_lock_peppol_invoices = self.env['account.move']
        for invoice, invoice_data in invoices_data.items():
            partner = invoice.partner_id.commercial_partner_id.with_company(invoice.company_id)
            if 'peppol' in invoice_data['sending_methods'] and self._is_applicable_to_move('peppol', invoice, **invoice_data):

                if invoice_data.get('ubl_cii_xml_attachment_values'):
                    xml_file = invoice_data['ubl_cii_xml_attachment_values']['raw']
                    filename = invoice_data['ubl_cii_xml_attachment_values']['name']
                elif invoice.ubl_cii_xml_id and invoice.peppol_move_state not in ('processing', 'done'):
                    xml_file = invoice.ubl_cii_xml_id.raw
                    filename = invoice.ubl_cii_xml_id.name
                else:
                    invoice.peppol_move_state = 'error'
                    builder = invoice.partner_id.commercial_partner_id._get_edi_builder(invoice_data['invoice_edi_format'])
                    invoice_data['error'] = _(
                        "Errors occurred while creating the EDI document (format: %s):",
                        builder._description
                    )
                    continue

                if invoice.invoice_pdf_report_id and self._needs_ubl_postprocessing(invoice_data):
                    self._postprocess_invoice_ubl_xml(invoice, invoice_data)
                    xml_file = invoice_data['ubl_cii_xml_attachment_values']['raw']
                    filename = invoice_data['ubl_cii_xml_attachment_values']['name']

                if len(xml_file) > 64000000:
                    invoice_data['error'] = _("Invoice %s is too big to send via peppol (64MB limit)", invoice.name)
                    continue

                receiver_identification = f"{partner.peppol_eas}:{partner.peppol_endpoint}"
                params['documents'].append({
                    'filename': filename,
                    'receiver': receiver_identification,
                    'ubl': b64encode(xml_file).decode(),
                })
                invoices_data_peppol[invoice] = invoice_data
                to_lock_peppol_invoices |= invoice

        if not params['documents']:
            return

        edi_user = next(iter(invoices_data)).company_id.account_peppol_edi_user

        if not self.env['res.company']._with_locked_records(to_lock_peppol_invoices, allow_raising=False):
            _logger.error('Failed to lock invoices for Peppol sending')
            return

        try:
            response = edi_user._call_peppol_proxy(
                "/api/peppol/1/send_document",
                params=params,
            )
        except AccountEdiProxyError as e:
            for invoice, invoice_data in invoices_data_peppol.items():
                invoice.peppol_move_state = 'error'
                invoice_data['error'] = {'error_title': e.message}
        else:
            if error_vals := response.get('error'):
                # at the moment the only error that can happen here is ParticipantNotReady error
                for invoice, invoice_data in invoices_data_peppol.items():
                    invoice.peppol_move_state = 'error'
                    invoice_data['error'] = {
                        'error_title': get_peppol_error_message(self.env, error_vals),
                    }
            else:
                # the response only contains message uuids,
                # so we have to rely on the order to connect peppol messages to account.move
                attachments_linked_message = _("The invoice has been sent to the Peppol Access Point. The following attachments were sent with the XML:")
                attachments_not_linked_message = _("Some attachments could not be sent with the XML:")
                for message, (invoice, invoice_data) in zip(response['messages'], invoices_data_peppol.items()):
                    invoice.peppol_message_uuid = message['message_uuid']
                    invoice.peppol_move_state = 'processing'
                    attachments_linked, attachments_not_linked = self._get_ubl_available_attachments(
                        invoice_data.get('mail_attachments_widget', []),
                        invoice_data['invoice_edi_format']
                    )
                    if attachments_not_linked:
                        invoice._message_log(body=attachments_not_linked_message, attachment_ids=attachments_not_linked.mapped('id'))

                    base_attachments = [
                        (invoice_data[key]['name'], invoice_data[key]['raw'])
                        for key in ['pdf_attachment_values', 'ubl_cii_xml_attachment_values']
                        if invoice_data.get(key)
                    ]

                    attachments_embedded = [
                        (attachment.name, attachment.raw)
                        for attachment in attachments_linked
                    ] + base_attachments

                    new_message = invoice.with_context(no_document=True).message_post(
                        body=attachments_linked_message,
                        attachments=attachments_embedded
                    )

                    if new_message.attachment_ids.ids:
                        if invoice.message_main_attachment_id in new_message.attachment_ids:
                            invoice.message_main_attachment_id = None
                        self.env.cr.execute("UPDATE ir_attachment SET res_id = NULL WHERE id IN %s", [tuple(new_message.attachment_ids.ids)])
                        new_message.attachment_ids.invalidate_recordset(['res_id', 'res_model'], flush=False)
                        new_message.attachment_ids.write({
                            'res_model': new_message._name,
                            'res_id': new_message.id,
                        })
                self.env.ref('account_peppol.ir_cron_peppol_get_message_status')._trigger(at=fields.Datetime.now() + timedelta(minutes=5))

        if self._can_commit():
            self.env.cr.commit()