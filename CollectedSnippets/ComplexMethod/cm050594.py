def _action_add_members(self, target_partners, member_status='joined', raise_on_access=False):
        """ Adds the target_partners as attendees of the channel(s).
            Partners are added as follows, depending on the value of member_status:
            1) (Default) 'joined'. The partners will be added as enrolled attendees. This will make the content
                (slides) of the channel available to that partner. This can also happen when an invited attendee
                enrolls themself. The attendees are also subscribed to the chatter of the channel.
                :return: the union of previous partners re-enrolling, new attendees and invited ones enrolling.
            2) 'invited' : This is used when inviting partners. The partners are added as invited attendees
                This will make the channel accessible but not the slides until they enroll themselves.
                :return: returns the union of new records and the ones unarchived.
        """
        SlideChannelPartnerSudo = self.env['slide.channel.partner'].sudo()
        allowed_channels = self._filter_add_members(raise_on_access=raise_on_access)
        if not allowed_channels or not target_partners:
            return SlideChannelPartnerSudo

        existing_channel_partners = self.env['slide.channel.partner'].with_context(active_test=False).sudo().search([
            ('channel_id', 'in', allowed_channels.ids),
            ('partner_id', 'in', target_partners.ids)
        ])

        # Unarchive existing channel partners, recomputing their completion and updating member_status
        archived_channel_partners = existing_channel_partners.filtered(lambda channel_partner: not channel_partner.active)
        to_unarchived = SlideChannelPartnerSudo
        if archived_channel_partners:
            archived_channel_partners.action_unarchive()
            to_unarchived = archived_channel_partners
            # Update member_status (and completion if enrolling)
            to_unarchived.member_status = member_status
            if member_status == 'joined':
                to_unarchived._recompute_completion()

        existing_channel_partners_map = defaultdict(lambda: self.env['slide.channel.partner'])
        for channel_partner in existing_channel_partners:
            existing_channel_partners_map[channel_partner.channel_id] += channel_partner

        # Invited partners confirming their invitation by enrolling, or upgraded to 'joined'.
        to_update_as_joined = SlideChannelPartnerSudo
        to_create_channel_partners_values = []

        for channel in allowed_channels:
            channel_partners = existing_channel_partners_map[channel]
            if member_status == 'joined':
                to_update_as_joined += channel_partners.filtered(lambda cp: cp.member_status == 'invited')
            for partner in target_partners - channel_partners.partner_id:
                to_create_channel_partners_values.append(dict(channel_id=channel.id, partner_id=partner.id, member_status=member_status))

        new_slide_channel_partners = SlideChannelPartnerSudo.create(to_create_channel_partners_values)
        to_update_as_joined.member_status = 'joined'
        to_update_as_joined._recompute_completion()

        # All fragments are in sudo.
        result_channel_partners = to_unarchived + to_update_as_joined + new_slide_channel_partners

        # Subscribe partners joining the course to the chatter.
        if member_status == 'joined':
            result_channel_partners_map = defaultdict(list)
            for channel_partner in result_channel_partners:
                result_channel_partners_map[channel_partner.channel_id].append(channel_partner.partner_id.id)
            for channel, partner_ids in result_channel_partners_map.items():
                channel.message_subscribe(
                    partner_ids=partner_ids,
                    subtype_ids=[self.env.ref('website_slides.mt_channel_slide_published').id]
                )
        return result_channel_partners