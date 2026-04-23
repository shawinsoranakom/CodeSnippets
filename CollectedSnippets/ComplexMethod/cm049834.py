def _compute_linked_message_ids(self):
        """ Compute the linked messages from the body of the message."""
        message_ids_by_message = defaultdict(list)
        for message in self:
            if tools.is_html_empty(message.body):
                continue
            str_ids = html.fromstring(message.body).xpath(
                "//a[contains(@class, 'o_message_redirect') and @data-oe-model='mail.message']/@data-oe-id",
            )
            for str_id in str_ids:
                with contextlib.suppress(ValueError, TypeError):
                    message_ids_by_message[message].append(int(str_id))
        mids = [mid for mids in message_ids_by_message.values() for mid in mids]
        if not mids:
            self.linked_message_ids = self.env["mail.message"]
            return
        # Remove any potential sudo from the env as linked messages are user input, returning them
        # as sudo could lead to users being able to read any arbitrary message through this feature.
        # Only allowed messages for the current user are acceptable.
        linked_messages = self.sudo(False).search(Domain("id", "in", mids))
        for message in self:
            message.linked_message_ids = linked_messages.filtered(
                lambda m, message=message: m.id in message_ids_by_message[message],
            )