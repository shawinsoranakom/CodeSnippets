def _notify_thread_with_out_of_office_get_additional_users(self, message, recipients_data, ooo_author, msg_vals=False):
        """ Fetch additional users which should send their OOO message.
        This includes users that are not directly pinged by message but
        are important for functional flows :

          - record responsible
          - parent message author (if internal user)
        """
        pids = [r['id'] for r in recipients_data if r['id']]
        additional_users_su = self.env['res.users'].sudo()
        if self and 'user_id' in self:
            additional_users_su += self.user_id.sudo().filtered(lambda u: u.partner_id != ooo_author)

        parent_msg = self.env['mail.message'].sudo()
        if (msg_vals or {}).get('parent_id'):
            parent_msg = self.env['mail.message'].sudo().browse(msg_vals['parent_id'])
        elif 'parent_id' not in (msg_vals or {}):
            parent_msg = message.parent_id
        parent_author = parent_msg.author_id if parent_msg.author_id.active else self.env['res.partner']
        if parent_author and parent_author.id not in pids and parent_author != ooo_author and not parent_msg.author_id.partner_share:
            additional_users_su |= parent_msg.author_id.main_user_id
        return additional_users_su