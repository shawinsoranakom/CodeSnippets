def _get_alerts(self):
        self.ensure_one()
        alerts = {}
        has_account_group = self.env.user.has_groups('account.group_account_readonly,account.group_account_invoice')

        if self.state == 'draft':
            if has_account_group and self.tax_lock_date_message:
                alerts['account_tax_lock_date'] = {
                    'level': 'warning',
                    'message': self.tax_lock_date_message,
                }
            if self.auto_post == 'at_date':
                alerts['account_auto_post_at_date'] = {
                    'level': 'info',
                    'message': _("This move is configured to be posted automatically at the accounting date: %s.", self.date),
                }
            if self.auto_post in ('yearly', 'quarterly', 'monthly'):
                message = _(
                    "%(auto_post_name)s auto-posting enabled. Next accounting date: %(move_date)s.",
                    auto_post_name=self.auto_post,
                    move_date=self.date,
                )
                if self.auto_post_until:
                    message += " "
                    message += _("The recurrence will end on %s (included).", self.auto_post_until)
                alerts['account_auto_post_on_period'] = {
                    'level': 'info',
                    'message': message,
                }
            if (
                self.is_purchase_document(include_receipts=True)
                and (zero_lines := self.invoice_line_ids.filtered(lambda line: line.price_total == 0))
                and len(zero_lines) >= 2
            ):
                alerts['account_remove_empty_lines'] = {
                    'level': 'info',
                    'message': _("We've noticed some empty lines on your invoice."),
                    'action_text': _("Remove empty lines"),
                    'action_call': ('account.move.line', 'unlink', zero_lines.ids),
                }

        if self.is_being_sent:
            alerts['account_is_being_sent'] = {
                'level': 'info',
                'message': _("This invoice is being sent in the background."),
            }
        if has_account_group and self.partner_credit_warning:
            alerts['account_partner_credit_warning'] = {
                'level': 'warning',
                'message': self.partner_credit_warning,
            }
        if self.abnormal_amount_warning:
            alerts['account_abnormal_amount_warning'] = {
                'level': 'warning',
                'message': self.abnormal_amount_warning,
            }
        if self.abnormal_date_warning:
            alerts['account_abnormal_date_warning'] = {
                'level': 'warning',
                'message': self.abnormal_date_warning,
            }

        return alerts