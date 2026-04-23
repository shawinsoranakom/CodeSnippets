def _get_channel_history(self):
        """
        Converting message body back to plaintext for correct data formatting in HTML field.
        """
        self.ensure_one()
        parts = []
        previous_message_author = None
        # sudo - mail.message: visitors can access messages on chats they have access to
        messages = self.sudo().chatbot_message_ids.mail_message_id or self.message_ids
        # sudo - mail.message: getting empty/notification messages to exclude them is allowed.
        filtered_messages = (
            messages.sudo().filtered(lambda m: m.message_type != "notification")
            - messages.sudo()._filter_empty()
        )
        for message in filtered_messages.sorted("id"):
            # sudo - res.partner: accessing livechat username or name is allowed to visitor
            message_author = message.author_id.sudo() or message.author_guest_id
            if previous_message_author != message_author:
                parts.append(
                    Markup("<br/><strong>%s:</strong><br/>")
                    % (
                        (message_author.user_livechat_username if message_author._name == "res.partner" else None)
                        or message_author.name
                    ),
                )
            if not tools.is_html_empty(message.body):
                parts.append(Markup("%s<br/>") % html2plaintext(message.body))
                previous_message_author = message_author
            for attachment in message.attachment_ids:
                previous_message_author = message_author
                # sudo - ir.attachment: public user can read attachment metadata
                parts.append(Markup("%s<br/>") % self._attachment_to_html(attachment.sudo()))
        return Markup("").join(parts)