def _notify_get_recipients_for_extra_notifications(self, message, recipients_data, msg_vals=False):
        """ Never send to author and to people outside Odoo (email) except comments """
        notif_pids = []
        notif_pids_notinbox = []
        for recipient in (r for r in recipients_data if r['active'] and r['id']):
            notif_pids.append(recipient['id'])
            if recipient['notif'] != 'inbox':
                notif_pids_notinbox.append(recipient['id'])
        if not notif_pids:
            return []

        msg_vals = msg_vals or {}
        msg_type = msg_vals.get('message_type') or message.sudo().message_type
        author_ids = [msg_vals.get('author_id') or message.sudo().author_id.id]
        if msg_type in {'comment', 'whatsapp_message'}:
            return set(notif_pids) - set(author_ids)
        elif msg_type in ('notification', 'user_notification', 'email'):
            return (set(notif_pids) - set(author_ids) - set(notif_pids_notinbox))
        return []