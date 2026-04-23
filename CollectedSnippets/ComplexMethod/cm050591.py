def create(self, vals_list):
        for vals in vals_list:
            # Ensure creator is member of its channel it is easier for them to manage it (unless it is odoobot)
            if not vals.get('channel_partner_ids') and not self.env.is_superuser():
                vals['channel_partner_ids'] = [(0, 0, {
                    'partner_id': self.env.user.partner_id.id
                })]
            if not is_html_empty(vals.get('description')) and is_html_empty(vals.get('description_short')):
                vals['description_short'] = vals['description']

        channels = super(SlideChannel, self.with_context(mail_create_nosubscribe=True)).create(vals_list)

        for channel in channels:
            if channel.user_id:
                channel._action_add_members(channel.user_id.partner_id)
            if channel.enroll_group_ids:
                channel._add_groups_members()

        return channels