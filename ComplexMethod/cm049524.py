def _call_web_service_after_invoice_pdf_render(self, invoices_data):
        # EXTENDS 'account'
        super()._call_web_service_after_invoice_pdf_render(invoices_data)

        params = {'documents': []}
        invoices_data_nemhandel = {}
        for invoice, invoice_data in invoices_data.items():
            partner = invoice.partner_id.commercial_partner_id.with_company(invoice.company_id)
            if 'nemhandel' not in invoice_data['sending_methods']:
                continue

            if not partner.nemhandel_identifier_type or not partner.nemhandel_identifier_value:
                invoice.nemhandel_move_state = 'error'
                invoice_data['error'] = _('The partner is missing Nemhandel Endpoint Type or Value.')
                continue

            if partner._get_nemhandel_verification_state(invoice_data['invoice_edi_format']) != 'valid':
                invoice.nemhandel_move_state = 'error'
                invoice_data['error'] = _('Please verify partner configuration in partner settings.')
                continue

            if not self._is_applicable_to_move('nemhandel', invoice, **invoice_data):
                continue

            if invoice_data.get('ubl_cii_xml_attachment_values'):
                xml_file = invoice_data['ubl_cii_xml_attachment_values']['raw']
                filename = invoice_data['ubl_cii_xml_attachment_values']['name']
            elif invoice.ubl_cii_xml_id and invoice.nemhandel_move_state not in {'processing', 'done'}:
                xml_file = invoice.ubl_cii_xml_id.raw
                filename = invoice.ubl_cii_xml_id.name
            else:
                invoice.nemhandel_move_state = 'error'
                builder = invoice.partner_id.commercial_partner_id._get_edi_builder(invoice_data['invoice_edi_format'])
                invoice_data['error'] = _(
                    "Errors occurred while creating the EDI document (format: %s):",
                    builder._description,
                )
                continue

            receiver_identification = f"{partner.nemhandel_identifier_type}:{partner.nemhandel_identifier_value}"
            params['documents'].append({
                'filename': filename,
                'receiver': receiver_identification,
                'ubl': b64encode(xml_file).decode(),
            })
            invoices_data_nemhandel[invoice] = invoice_data

        if not params['documents']:
            return

        edi_user = next(iter(invoices_data)).company_id.nemhandel_edi_user

        try:
            response = edi_user._call_nemhandel_proxy(
                "/api/nemhandel/1/send_document",
                params=params,
            )
        except UserError as e:
            for invoice, invoice_data in invoices_data_nemhandel.items():
                invoice.nemhandel_move_state = 'error'
                invoice_data['error'] = str(e)
        else:
            if response.get('error'):
                # at the moment the only error that can happen here is ParticipantNotReady error
                for invoice, invoice_data in invoices_data_nemhandel.items():
                    invoice.nemhandel_move_state = 'error'
                    invoice_data['error'] = response['error']['message']
            else:
                # the response only contains message uuids,
                # so we have to rely on the order to connect nemhandel messages to account.move
                invoices = self.env['account.move']
                for message, (invoice, invoice_data) in zip(response['messages'], invoices_data_nemhandel.items()):
                    invoice.nemhandel_message_uuid = message['message_uuid']
                    invoice.nemhandel_move_state = 'processing'
                    invoices |= invoice
                log_message = _('The document has been sent to the Nemhandel Access Point for processing')
                invoices._message_log_batch(bodies={invoice.id: log_message for invoice in invoices})
                self.env.ref('l10n_dk_nemhandel.ir_cron_nemhandel_get_message_status')._trigger(at=fields.Datetime.now() + timedelta(minutes=5))

        if self._can_commit():
            self.env.cr.commit()