def _res_for_member(self, channel, partner=None, guest=None):
        members = channel.channel_member_ids
        member_0 = members.filtered(lambda m: m.partner_id == self.users[0].partner_id)
        member_0_last_interest_dt = fields.Datetime.to_string(member_0.last_interest_dt)
        member_0_last_seen_dt = fields.Datetime.to_string(member_0.last_seen_dt)
        member_0_create_date = fields.Datetime.to_string(member_0.create_date)
        member_1 = members.filtered(lambda m: m.partner_id == self.users[1].partner_id)
        member_2 = members.filtered(lambda m: m.partner_id == self.users[2].partner_id)
        member_3 = members.filtered(lambda m: m.partner_id == self.users[3].partner_id)
        member_12 = members.filtered(lambda m: m.partner_id == self.users[12].partner_id)
        member_14 = members.filtered(lambda m: m.partner_id == self.users[14].partner_id)
        member_15 = members.filtered(lambda m: m.partner_id == self.users[15].partner_id)
        last_message = channel._get_last_messages()
        last_message_of_partner_0 = self.env["mail.message"].search(
            Domain("author_id", "=", member_0.partner_id.id)
            & Domain("model", "=", "discuss.channel")
            & Domain("res_id", "=", channel.id),
            order="id desc",
            limit=1,
        )
        member_g = members.filtered(lambda m: m.guest_id)
        guest = member_g.guest_id
        # sudo: bus.bus: reading non-sensitive last id
        bus_last_id = self.env["bus.bus"].sudo()._bus_last_id()
        if channel == self.channel_general and partner == self.users[0].partner_id:
            return {
                "create_date": member_0_create_date,
                "custom_channel_name": False,
                "custom_notifications": False,
                "fetched_message_id": False,
                "id": member_0.id,
                "last_interest_dt": member_0_last_interest_dt,
                "message_unread_counter": 1,
                "message_unread_counter_bus_id": bus_last_id,
                "mute_until_dt": False,
                "last_seen_dt": member_0_last_seen_dt,
                "new_message_separator": 0,
                "partner_id": self.users[0].partner_id.id,
                "rtc_inviting_session_id": False,
                "seen_message_id": False,
                "unpin_dt": False,
                "channel_id": {"id": channel.id, "model": "discuss.channel"},
            }
        if channel == self.channel_channel_public_1 and partner == self.users[0].partner_id:
            return {
                "create_date": member_0_create_date,
                "custom_channel_name": False,
                "custom_notifications": False,
                "fetched_message_id": last_message.id,
                "id": member_0.id,
                "last_interest_dt": member_0_last_interest_dt,
                "message_unread_counter": 0,
                "message_unread_counter_bus_id": bus_last_id,
                "mute_until_dt": False,
                "last_seen_dt": member_0_last_seen_dt,
                "new_message_separator": last_message.id + 1,
                "partner_id": self.users[0].partner_id.id,
                "rtc_inviting_session_id": False,
                "seen_message_id": last_message.id,
                "unpin_dt": False,
                "channel_id": {"id": channel.id, "model": "discuss.channel"},
            }
        if channel == self.channel_channel_public_2 and partner == self.users[0].partner_id:
            return {
                "create_date": member_0_create_date,
                "custom_channel_name": False,
                "custom_notifications": False,
                "fetched_message_id": last_message.id,
                "id": member_0.id,
                "last_interest_dt": member_0_last_interest_dt,
                "message_unread_counter": 0,
                "message_unread_counter_bus_id": bus_last_id,
                "mute_until_dt": False,
                "last_seen_dt": member_0_last_seen_dt,
                "new_message_separator": last_message.id + 1,
                "partner_id": self.users[0].partner_id.id,
                "rtc_inviting_session_id": False,
                "seen_message_id": last_message.id,
                "unpin_dt": False,
                "channel_id": {"id": channel.id, "model": "discuss.channel"},
            }
        if channel == self.channel_channel_group_1 and partner == self.users[0].partner_id:
            return {
                "create_date": member_0_create_date,
                "custom_channel_name": False,
                "custom_notifications": False,
                "fetched_message_id": last_message_of_partner_0.id,
                "id": member_0.id,
                "last_interest_dt": member_0_last_interest_dt,
                "message_unread_counter": 0,
                "message_unread_counter_bus_id": bus_last_id,
                "mute_until_dt": False,
                "last_seen_dt": member_0_last_seen_dt,
                "new_message_separator": last_message_of_partner_0.id + 1,
                "partner_id": self.users[0].partner_id.id,
                "rtc_inviting_session_id": member_0.rtc_inviting_session_id.id,
                "seen_message_id": last_message_of_partner_0.id,
                "unpin_dt": False,
                "channel_id": {"id": channel.id, "model": "discuss.channel"},
            }
        if channel == self.channel_channel_group_1 and partner == self.users[2].partner_id:
            return {
                "id": member_2.id,
                "partner_id": self.users[2].partner_id.id,
                "channel_id": {"id": channel.id, "model": "discuss.channel"},
            }
        if channel == self.channel_channel_group_2 and partner == self.users[0].partner_id:
            return {
                "create_date": member_0_create_date,
                "custom_channel_name": False,
                "custom_notifications": False,
                "fetched_message_id": last_message.id,
                "id": member_0.id,
                "last_interest_dt": member_0_last_interest_dt,
                "message_unread_counter": 0,
                "message_unread_counter_bus_id": bus_last_id,
                "mute_until_dt": False,
                "last_seen_dt": member_0_last_seen_dt,
                "new_message_separator": last_message.id + 1,
                "partner_id": self.users[0].partner_id.id,
                "rtc_inviting_session_id": False,
                "seen_message_id": last_message.id,
                "unpin_dt": False,
                "channel_id": {"id": channel.id, "model": "discuss.channel"},
            }
        if channel == self.channel_group_1 and partner == self.users[0].partner_id:
            return {
                "create_date": member_0_create_date,
                "custom_channel_name": False,
                "custom_notifications": False,
                "fetched_message_id": False,
                "id": member_0.id,
                "last_interest_dt": member_0_last_interest_dt,
                "message_unread_counter": 0,
                "message_unread_counter_bus_id": bus_last_id,
                "mute_until_dt": False,
                "last_seen_dt": member_0_last_seen_dt,
                "new_message_separator": 0,
                "partner_id": self.users[0].partner_id.id,
                "rtc_inviting_session_id": False,
                "seen_message_id": False,
                "unpin_dt": False,
                "channel_id": {"id": channel.id, "model": "discuss.channel"},
            }
        if channel == self.channel_group_1 and partner == self.users[12].partner_id:
            return {
                "create_date": fields.Datetime.to_string(member_12.create_date),
                "last_seen_dt": False,
                "fetched_message_id": False,
                "id": member_12.id,
                "partner_id": self.users[12].partner_id.id,
                "seen_message_id": False,
                "channel_id": {"id": channel.id, "model": "discuss.channel"},
            }
        if channel == self.channel_chat_1 and partner == self.users[0].partner_id:
            return {
                "create_date": member_0_create_date,
                "custom_channel_name": False,
                "custom_notifications": False,
                "fetched_message_id": False,
                "id": member_0.id,
                "last_interest_dt": member_0_last_interest_dt,
                "message_unread_counter": 0,
                "message_unread_counter_bus_id": bus_last_id,
                "mute_until_dt": False,
                "last_seen_dt": member_0_last_seen_dt,
                "new_message_separator": 0,
                "partner_id": self.users[0].partner_id.id,
                "rtc_inviting_session_id": False,
                "seen_message_id": False,
                "unpin_dt": False,
                "channel_id": {"id": channel.id, "model": "discuss.channel"},
            }
        if channel == self.channel_chat_1 and partner == self.users[14].partner_id:
            return {
                "create_date": fields.Datetime.to_string(member_14.create_date),
                "last_seen_dt": False,
                "fetched_message_id": False,
                "id": member_14.id,
                "partner_id": self.users[14].partner_id.id,
                "seen_message_id": False,
                "channel_id": {"id": channel.id, "model": "discuss.channel"},
            }
        if channel == self.channel_chat_2 and partner == self.users[0].partner_id:
            return {
                "create_date": member_0_create_date,
                "custom_channel_name": False,
                "custom_notifications": False,
                "fetched_message_id": False,
                "id": member_0.id,
                "last_interest_dt": member_0_last_interest_dt,
                "message_unread_counter": 0,
                "message_unread_counter_bus_id": bus_last_id,
                "mute_until_dt": False,
                "last_seen_dt": member_0_last_seen_dt,
                "new_message_separator": 0,
                "partner_id": self.users[0].partner_id.id,
                "rtc_inviting_session_id": False,
                "seen_message_id": False,
                "unpin_dt": False,
                "channel_id": {"id": channel.id, "model": "discuss.channel"},
            }
        if channel == self.channel_chat_2 and partner == self.users[15].partner_id:
            return {
                "create_date": fields.Datetime.to_string(member_15.create_date),
                "last_seen_dt": False,
                "fetched_message_id": False,
                "id": member_15.id,
                "partner_id": self.users[15].partner_id.id,
                "seen_message_id": False,
                "channel_id": {"id": channel.id, "model": "discuss.channel"},
            }
        if channel == self.channel_chat_3 and partner == self.users[0].partner_id:
            return {
                "create_date": member_0_create_date,
                "custom_channel_name": False,
                "custom_notifications": False,
                "fetched_message_id": False,
                "id": member_0.id,
                "last_interest_dt": member_0_last_interest_dt,
                "message_unread_counter": 0,
                "message_unread_counter_bus_id": bus_last_id,
                "mute_until_dt": False,
                "last_seen_dt": member_0_last_seen_dt,
                "new_message_separator": 0,
                "partner_id": self.users[0].partner_id.id,
                "rtc_inviting_session_id": False,
                "seen_message_id": False,
                "unpin_dt": False,
                "channel_id": {"id": channel.id, "model": "discuss.channel"},
            }
        if channel == self.channel_chat_3 and partner == self.users[2].partner_id:
            return {
                "create_date": fields.Datetime.to_string(member_2.create_date),
                "last_seen_dt": False,
                "fetched_message_id": False,
                "id": member_2.id,
                "partner_id": self.users[2].partner_id.id,
                "seen_message_id": False,
                "channel_id": {"id": channel.id, "model": "discuss.channel"},
            }
        if channel == self.channel_chat_4 and partner == self.users[0].partner_id:
            return {
                "create_date": member_0_create_date,
                "custom_channel_name": False,
                "custom_notifications": False,
                "fetched_message_id": False,
                "id": member_0.id,
                "last_interest_dt": member_0_last_interest_dt,
                "message_unread_counter": 0,
                "message_unread_counter_bus_id": bus_last_id,
                "mute_until_dt": False,
                "last_seen_dt": member_0_last_seen_dt,
                "new_message_separator": 0,
                "partner_id": self.users[0].partner_id.id,
                "rtc_inviting_session_id": False,
                "seen_message_id": False,
                "unpin_dt": False,
                "channel_id": {"id": channel.id, "model": "discuss.channel"},
            }
        if channel == self.channel_chat_4 and partner == self.users[3].partner_id:
            return {
                "create_date": fields.Datetime.to_string(member_3.create_date),
                "last_seen_dt": False,
                "fetched_message_id": False,
                "id": member_3.id,
                "partner_id": self.users[3].partner_id.id,
                "seen_message_id": False,
                "channel_id": {"id": channel.id, "model": "discuss.channel"},
            }
        if channel == self.channel_livechat_1 and partner == self.users[0].partner_id:
            return {
                "create_date": member_0_create_date,
                "custom_channel_name": False,
                "custom_notifications": False,
                "fetched_message_id": False,
                "id": member_0.id,
                "livechat_member_type": "agent",
                "last_interest_dt": member_0_last_interest_dt,
                "message_unread_counter": 1,
                "message_unread_counter_bus_id": bus_last_id,
                "mute_until_dt": False,
                "last_seen_dt": member_0_last_seen_dt,
                "new_message_separator": 0,
                "partner_id": self.users[0].partner_id.id,
                "rtc_inviting_session_id": False,
                "seen_message_id": False,
                "unpin_dt": fields.Datetime.to_string(member_0.unpin_dt),
                "channel_id": {"id": channel.id, "model": "discuss.channel"},
            }
        if channel == self.channel_livechat_1 and partner == self.users[1].partner_id:
            return {
                "create_date": fields.Datetime.to_string(member_1.create_date),
                "last_seen_dt": fields.Datetime.to_string(member_1.last_seen_dt),
                "fetched_message_id": last_message.id,
                "id": member_1.id,
                "livechat_member_type": "visitor",
                "partner_id": self.users[1].partner_id.id,
                "seen_message_id": last_message.id,
                "channel_id": {"id": channel.id, "model": "discuss.channel"},
            }
        if channel == self.channel_livechat_2 and partner == self.users[0].partner_id:
            return {
                "create_date": member_0_create_date,
                "custom_channel_name": False,
                "custom_notifications": False,
                "fetched_message_id": False,
                "id": member_0.id,
                "livechat_member_type": "agent",
                "last_interest_dt": member_0_last_interest_dt,
                "message_unread_counter": 1,
                "message_unread_counter_bus_id": bus_last_id,
                "mute_until_dt": False,
                "last_seen_dt": member_0_last_seen_dt,
                "new_message_separator": 0,
                "partner_id": self.users[0].partner_id.id,
                "rtc_inviting_session_id": False,
                "seen_message_id": False,
                "unpin_dt": fields.Datetime.to_string(member_0.unpin_dt),
                "channel_id": {"id": channel.id, "model": "discuss.channel"},
            }
        if channel == self.channel_livechat_2 and guest:
            return {
                "create_date": fields.Datetime.to_string(member_g.create_date),
                "last_seen_dt": fields.Datetime.to_string(member_g.last_seen_dt),
                "fetched_message_id": last_message.id,
                "id": member_g.id,
                "livechat_member_type": "visitor",
                "guest_id": guest.id,
                "seen_message_id": last_message.id,
                "channel_id": {"id": channel.id, "model": "discuss.channel"},
            }
        return {}