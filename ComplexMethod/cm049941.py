def _notify_by_web_push_prepare_payload(self, message, msg_vals=False, force_record_name=False):
        payload = super()._notify_by_web_push_prepare_payload(
            message, msg_vals=msg_vals, force_record_name=force_record_name,
        )
        msg_vals = msg_vals or {}
        payload['options']['data']['action'] = 'mail.action_discuss'
        record_name = force_record_name or message.record_name
        author_ids = [msg_vals["author_id"]] if msg_vals.get("author_id") else message.author_id.ids
        author = self.env["res.partner"].browse(author_ids) or self.env["mail.guest"].browse(
            msg_vals.get("author_guest_id", message.author_guest_id.id)
        )
        if self.channel_type == 'chat':
            payload['title'] = author.name
        elif self.channel_type == 'channel':
            payload['title'] = "#%s - %s" % (record_name, author.name)
        elif self.channel_type == 'group':
            if not record_name:
                member_names = self.channel_member_ids.mapped(lambda m: m.partner_id.name if m.partner_id else m.guest_id.name)
                record_name = f"{', '.join(member_names[:-1])} and {member_names[-1]}" if len(member_names) > 1 else member_names[0] if member_names else ""
            payload['title'] = "%s - %s" % (record_name, author.name)
        else:
            payload['title'] = "#%s" % (record_name)
        return payload