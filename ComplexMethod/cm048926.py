def _postprocess_cancel_edi_results(documents, edi_result):
            move_ids_to_cancel = set()  # Avoid duplicates
            attachments_to_unlink = self.env['ir.attachment']
            for document in documents:
                move = document.move_id
                move_result = edi_result.get(move, {})
                if move_result.get('success') is True:
                    old_attachment = document.sudo().attachment_id
                    document.sudo().write({
                        'state': 'cancelled',
                        'error': False,
                        'attachment_id': False,
                        'blocking_level': False,
                    })

                    if move.state == 'posted' and all(
                        doc.state == 'cancelled'
                        or not doc.edi_format_id._needs_web_services()
                        for doc in move.edi_document_ids
                    ):
                        # The user requested a cancellation of the EDI and it has been approved. Then, the invoice
                        # can be safely cancelled.
                        move_ids_to_cancel.add(move.id)

                    if not old_attachment.res_model or not old_attachment.res_id:
                        attachments_to_unlink |= old_attachment

                else:
                    document.write({
                        'error': move_result.get('error', False),
                        'blocking_level': move_result.get('blocking_level', DEFAULT_BLOCKING_LEVEL) if move_result.get('error') else False,
                    })

            if move_ids_to_cancel:
                invoices = self.env['account.move'].browse(list(move_ids_to_cancel))
                invoices.button_draft()
                invoices.button_cancel()

            # Attachments that are not explicitly linked to a business model could be removed because they are not
            # supposed to have any traceability from the user.
            attachments_to_unlink.sudo().unlink()