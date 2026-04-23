def button_cancel_posted_moves(self):
        '''Mark the edi.document related to this move to be canceled.
        '''
        to_cancel_documents = self.env['account.edi.document']
        for move in self:
            move._check_fiscal_lock_dates()
            is_move_marked = False
            for doc in move.edi_document_ids:
                move_applicability = doc.edi_format_id._get_move_applicability(move)
                if doc.edi_format_id._needs_web_services() \
                        and doc.state == 'sent' \
                        and move_applicability \
                        and move_applicability.get('cancel'):
                    to_cancel_documents |= doc
                    is_move_marked = True
            if is_move_marked:
                move.message_post(body=_("A cancellation of the EDI has been requested."))

        to_cancel_documents.write({'state': 'to_cancel', 'error': False, 'blocking_level': False})