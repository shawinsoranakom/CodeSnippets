def _generate_mail_notification_values(self, mails):
        if self.auto_delete and not self.auto_delete_keep_log:
            return []

        create_vals_all = []
        for mail, notif_base_values in zip(mails, mails._get_notification_values()):
            emails = set(tools.mail.email_split_and_format_normalize(f'{mail.email_to or ""}, {mail.email_cc or ""}'))
            emails = emails or ([mail.email_to] if mail.email_to else "")

            # if no recipient, the email will have mail_email_missing failure_type
            if not mail.recipient_ids and not emails:
                create_vals_all.append(notif_base_values)
            else:
                create_vals_all.extend(notif_base_values | {'res_partner_id': partner.id} for partner in mail.recipient_ids)
                create_vals_all.extend(notif_base_values | {'mail_email_address': email} for email in emails)
        return create_vals_all