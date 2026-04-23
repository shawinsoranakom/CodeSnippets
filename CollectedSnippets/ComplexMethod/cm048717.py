def _get_alerts(self, moves, moves_data):
        """ Returns a dict of all alerts corresponding to moves with the given context (sending method,
        edi format to generate, extra_edi to generate).
        An alert can have some information:
        - level (danger, info, warning, ...)  (! danger alerts are considered blocking and will be raised)
        - message to display
        - action_text for the text to show on the clickable link
        - action the action to run when the link is clicked
        """
        alerts = {}
        send_cron = self.env.ref('account.ir_cron_account_move_send', raise_if_not_found=False)
        if len(moves) > 1 and send_cron and not send_cron.sudo().active:
            has_cron_access = send_cron.has_access('write')
            has_access_message = _("The scheduled action 'Send Invoices automatically' is archived. You won't be able to send invoices in batch.")
            no_access_addendum = _("\nPlease contact your administrator.")
            alerts['account_send_cron_archived'] = {
                'level': 'warning',
                'message': has_access_message if has_cron_access else has_access_message + no_access_addendum,
                'action_text': _("Check") if has_cron_access else None,
                'action': send_cron._get_records_action() if has_cron_access else None,
            }
        # Filter moves that are trying to send via email
        email_moves = moves.filtered(lambda m: 'email' in moves_data[m]['sending_methods'])
        if email_moves:
            # Identify partners without email depending on batch/single send
            if is_batch := len(moves) > 1:
                # Batch sending
                partners_without_mail = email_moves.filtered(lambda m: not m.partner_id.email).mapped('partner_id')
            else:
                # Single sending
                partners_without_mail = moves_data[email_moves]['mail_partner_ids'].filtered(lambda p: not p.email)

            # If there are partners without email, add an alert
            if partners_without_mail:
                alerts['account_missing_email'] = {
                    'level': 'warning' if is_batch else 'danger',
                    'message': _("Partner(s) should have an email address."),
                    'action_text': _("View Partner(s)") if is_batch else False,
                    'action': (
                        partners_without_mail._get_records_action(name=_("Check Partner(s) Email(s)"))
                        if is_batch else False
                    ),
                }

        return alerts