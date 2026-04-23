def _call_web_service_after_invoice_pdf_render(self, invoices_data):
        # EXTENDS 'account'
        super()._call_web_service_after_invoice_pdf_render(invoices_data)
        attachments_vals = {}
        moves = self.env['account.move']

        # Filter only l10n_it_edi attachments
        moves_data = {
            move: move_data
            for move, move_data in invoices_data.items()
            if 'it_edi_send' in move_data['extra_edis']
        }

        # Prepare attachment data
        for move, move_data in moves_data.items():
            if attachment := move.l10n_it_edi_attachment_file:
                attachments_vals[move] = {'name': move.l10n_it_edi_attachment_name, 'raw': base64.b64decode(attachment)}
                moves |= move
            elif edi_values := move_data.get('l10n_it_edi_values'):
                attachments_vals[move] = edi_values
                moves |= move

        # Send
        results = moves._l10n_it_edi_send(attachments_vals)

        # Eventually update attachments with signed data
        for move, move_data in moves_data.items():
            if move.l10n_it_edi_attachment_file:
                attachment_name = move.l10n_it_edi_attachment_name
            elif attachment := move_data.get('l10n_it_edi_values'):
                attachment_name = attachment['name']
            attachment_data = results.get(attachment_name, {})
            if attachment_data.get('signed') and (signed_data := attachment_data.get('signed_data')):
                move.l10n_it_edi_attachment_file = base64.b64encode(signed_data.encode())
                # Show that those moves couldn't be sent
            if 'error_message' in attachment_data:
                moves_data[move]['error'] = {'error_title': attachment_data['error_message']}