def _add_members(
        self,
        *,
        guests=None,
        partners=None,
        users=None,
        create_member_params=None,
        invite_to_rtc_call=False,
        post_joined_message=True,
        inviting_partner=None,
    ):
        inviting_partner = inviting_partner or self.env["res.partner"]
        partners = partners or self.env["res.partner"]
        if users:
            partners |= users.partner_id
        guests = guests or self.env["mail.guest"]
        current_partner, current_guest = self.env["res.partner"]._get_current_persona()
        all_new_members = self.env["discuss.channel.member"]
        for channel in self:
            members_to_create = []
            existing_members = self.env['discuss.channel.member'].search(
                Domain('channel_id', '=', channel.id)
                & (Domain('partner_id', 'in', partners.ids) | Domain('guest_id', 'in', guests.ids))
            )
            members_to_create += [{
                **(create_member_params or {}),
                'partner_id': partner.id,
                'channel_id': channel.id,
            } for partner in partners - existing_members.partner_id]
            members_to_create += [{
                **(create_member_params or {}),
                'guest_id': guest.id,
                'channel_id': channel.id,
            } for guest in guests - existing_members.guest_id]
            if channel.parent_channel_id and channel.parent_channel_id.has_access("write"):
                new_members = self.env["discuss.channel.member"].sudo().create(members_to_create)
            else:
                new_members = self.env["discuss.channel.member"].create(members_to_create)
            all_new_members += new_members
            for member in new_members:
                payload = {
                    "channel_id": member.channel_id.id,
                    "invite_to_rtc_call": invite_to_rtc_call,
                    "data": Store(bus_channel=member._bus_channel())
                    .add(member.channel_id)
                    .add(member, "unpin_dt")
                    .get_result(),
                }
                if not member.is_self and not self.env.user._is_public():
                    payload["invited_by_user_id"] = self.env.user.id
                member._bus_send("discuss.channel/joined", payload)
                if channel.channel_type != "channel" and post_joined_message:
                    notification = (
                        _("joined the channel")
                        if member.is_self
                        else _("invited %s to the channel", member._get_html_link(for_persona=True))
                    )
                    member.channel_id.message_post(
                        author_id=inviting_partner.id or None,
                        body=Markup('<div class="o_mail_notification" data-oe-type="channel-joined">%s</div>') % notification,
                        message_type="notification",
                        subtype_xmlid="mail.mt_comment",
                    )
            if new_members:
                Store(bus_channel=channel).add(channel, "member_count").add(new_members).bus_send()
            if existing_members and (bus_channel := current_partner.main_user_id or current_guest):
                # If the current user invited these members but they are already present, notify the current user about their existence as well.
                # In particular this fixes issues where the current user is not aware of its own member in the following case:
                # create channel from form view, and then join from discuss without refreshing the page.
                Store(
                    bus_channel=bus_channel,
                ).add(channel, "member_count").add(existing_members).bus_send()
        if invite_to_rtc_call:
            for channel in self:
                current_channel_member = self.env['discuss.channel.member'].search([('channel_id', '=', channel.id), ('is_self', '=', True)])
                # sudo: discuss.channel.rtc.session - reading rtc sessions of current user
                if current_channel_member and current_channel_member.sudo().rtc_session_ids:
                    # sudo: discuss.channel.rtc.session - current user can invite new members in call
                    current_channel_member.sudo()._rtc_invite_members(member_ids=new_members.ids)
        return all_new_members