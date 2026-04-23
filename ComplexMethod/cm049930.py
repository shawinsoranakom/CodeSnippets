def create(self, vals_list):
        if self.env.context.get("mail_create_bypass_create_check") is self._bypass_create_check:
            self = self.sudo()
        for vals in vals_list:
            if "channel_id" not in vals:
                raise UserError(
                    _(
                        "It appears you're trying to create a channel member, but it seems like you forgot to specify the related channel. "
                        "To move forward, please make sure to provide the necessary channel information."
                    )
                )
            channel = self.env["discuss.channel"].browse(vals["channel_id"])
            if channel.channel_type == "chat" and len(channel.channel_member_ids) > 0:
                raise UserError(
                    _("Adding more members to this chat isn't possible; it's designed for just two people.")
                )
        name_members_by_channel = {
            channel: channel.channel_name_member_ids
            for channel in self.env["discuss.channel"].browse(
                {vals["channel_id"] for vals in vals_list}
            )
        }
        res = super().create(vals_list)
        # help the ORM to detect changes
        res.partner_id.invalidate_recordset(["channel_ids"])
        res.guest_id.invalidate_recordset(["channel_ids"])
        # Always link members to parent channels as well. Member list should be
        # kept in sync.
        for member in res:
            if parent := member.channel_id.parent_channel_id:
                parent._add_members(partners=member.partner_id, guests=member.guest_id)
        for channel, members in name_members_by_channel.items():
            if channel.channel_name_member_ids != members:
                Store(bus_channel=channel).add(
                    channel,
                    Store.Many("channel_name_member_ids", sort="id"),
                ).bus_send()
        return res