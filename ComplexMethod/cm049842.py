def _notify_message_notification_update(self):
        """Send bus notifications to update status of notifications in the web
        client. Purpose is to send the updated status per author."""
        messages = self.env['mail.message']
        record_by_message = self._record_by_message()
        for message in self:
            # Check if user has access to the record before displaying a notification about it.
            # In case the user switches from one company to another, it might happen that they don't
            # have access to the record related to the notification. In this case, we skip it.
            # YTI FIXME: check allowed_company_ids if necessary
            if record := record_by_message.get(message):
                try:
                    if record.has_access('read'):
                        _dummy = record.display_name  # access anything to make sure record exists
                        messages += message
                except (MissingError):
                    # record has been removed from db without cascading notif -> avoid crash at least
                    continue
        messages_per_partner = defaultdict(lambda: self.env['mail.message'])
        for message in messages:
            if not self.env.user._is_public():
                messages_per_partner[self.env.user.partner_id] |= message
            if message.author_id and not any(user._is_public() for user in message.author_id.with_context(active_test=False).user_ids):
                messages_per_partner[message.author_id] |= message
        for partner, messages in messages_per_partner.items():
            if user := partner.main_user_id:
                store = Store(bus_channel=user)
                messages.with_user(user)._message_notifications_to_store(store)
                store.bus_send()