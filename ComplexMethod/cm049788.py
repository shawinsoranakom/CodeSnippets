def _get_channel_id(self, user_key, channel_key, membership, sub_channel):
        user = self.env["res.users"] if user_key == "public" else self.users[user_key]
        partner = user.partner_id
        guest = self.guest if user_key == "public" else self.env["mail.guest"]
        partners = self.other_user.partner_id
        if membership == "member":
            partners += partner
        DiscussChannel = self.env["discuss.channel"].with_user(self.other_user)
        if channel_key == "group":
            channel = DiscussChannel._create_group(partners.ids)
            if membership == "member":
                channel._add_members(users=user, guests=guest)
        elif channel_key == "chat":
            channel = DiscussChannel._get_or_create_chat(partners.ids)
        else:
            channel = DiscussChannel._create_channel("Channel", group_id=None)
            if membership == "member":
                channel._add_members(users=user, guests=guest)
        if channel_key == "no_group":
            channel.group_public_id = None
        elif channel_key == "group_matching":
            channel.group_public_id = self.secret_group
        elif channel_key == "group_failing":
            channel.group_public_id = self.env.ref("base.group_system")
        if sub_channel:
            channel.sudo()._create_sub_channel()
            channel = channel.sub_channel_ids[0]
            if membership == "member":
                channel.sudo()._add_members(users=user, guests=guest)
        return channel.id