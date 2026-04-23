def _postprocess_sent_message(self, success_pids, success_emails, failure_reason=False, failure_type=None):
        """Perform any post-processing necessary after sending ``mail``
        successfully, including deleting it completely along with its
        attachment if the ``auto_delete`` flag of the mail was set.
        Overridden by subclasses for extra post-processing behaviors.

        :return: True
        """
        notif_mails_ids = [mail.id for mail in self if mail.is_notification]
        if notif_mails_ids:
            notifications = self.env['mail.notification'].search([
                ('notification_type', '=', 'email'),
                ('mail_mail_id', 'in', notif_mails_ids),
                ('notification_status', 'not in', ('sent', 'canceled'))
            ])
            if notifications:
                # find all notification linked to a failure
                failed = self.env['mail.notification']
                if failure_type:
                    failed = notifications.filtered(lambda notif:
                        notif.res_partner_id not in success_pids
                        and notif.mail_email_address not in success_emails
                    )
                (notifications - failed).sudo().write({
                    'notification_status': 'sent',
                    'failure_type': '',
                    'failure_reason': '',
                })
                if failed:
                    failed.sudo().write({
                        'notification_status': 'exception',
                        'failure_type': failure_type,
                        'failure_reason': failure_reason,
                    })
                    messages = notifications.mapped('mail_message_id').filtered(lambda m: m._is_thread_message())
                    # TDE TODO: could be great to notify message-based, not notifications-based, to lessen number of notifs
                    messages._notify_message_notification_update()  # notify user that we have a failure
        if not failure_type or failure_type in ['mail_email_invalid', 'mail_email_missing']:  # if we have another error, we want to keep the mail.
            self.sudo().filtered(lambda mail: mail.auto_delete).unlink()

        return True