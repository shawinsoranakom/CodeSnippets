def action_send_mail(self):
        self.ensure_one()

        # Reject
        if self.action == 'reject' and self.send_email:
            self.mail_group_message_id.action_moderate_reject_with_comment(self.subject, self.body)
        elif self.action == 'reject' and not self.send_email:
            self.mail_group_message_id.action_moderate_reject()

        # Ban
        elif self.action == 'ban' and self.send_email:
            self.mail_group_message_id.action_moderate_ban_with_comment(self.subject, self.body)
        elif self.action == 'ban' and not self.send_email:
            self.mail_group_message_id.action_moderate_ban()