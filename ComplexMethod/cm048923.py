def _compute_edi_show_cancel_button(self):
        for move in self:
            if move.state != 'posted':
                move.edi_show_cancel_button = False
                continue

            move.edi_show_cancel_button = False
            for doc in move.edi_document_ids:
                move_applicability = doc.edi_format_id._get_move_applicability(move)
                if doc.edi_format_id._needs_web_services() \
                    and doc.state == 'sent' \
                    and move_applicability \
                    and move_applicability.get('cancel'):
                    move.edi_show_cancel_button = True
                    break