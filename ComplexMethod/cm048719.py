def _hook_if_success(self, moves_data, from_cron=False):
        """ Process (typically send) successful documents."""
        group_by_partner = defaultdict(list)
        to_send_mail = {}
        for move, move_data in moves_data.items():
            if from_cron:
                group_by_partner[move_data['author_partner_id']].append(move.id)
            if 'email' in move_data['sending_methods'] and self._is_applicable_to_move('email', move, **move_data):
                to_send_mail[move] = move_data
        self._send_mails(to_send_mail)
        self._send_notifications_to_partners(group_by_partner)

        # Notify subscribers.
        for move, move_data in moves_data.items():
            if not move.is_invoice(include_receipts=True):
                continue

            try:
                move.journal_id._notify_invoice_subscribers(
                    invoice=move,
                    mail_params={
                        'attachment_ids': [
                            Command.create({'name': attachment.name, 'raw': attachment.raw, 'mimetype': attachment.mimetype})
                            for attachment in self._get_invoice_extra_attachments(move)
                        ]
                    },
                )
            except Exception:
                _logger.exception("Failed notifying subscribers for move %s", move.id)