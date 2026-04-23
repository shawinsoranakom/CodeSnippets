def _create_or_update_history(self, values_by_member):
        members_without_history = self.filtered(lambda m: not m.livechat_member_history_ids)
        history_domain = Domain.OR(
            [
                [
                    ("channel_id", "=", member.channel_id.id),
                    ("partner_id", "=", member.partner_id.id)
                    if member.partner_id
                    else ("guest_id", "=", member.guest_id.id),
                ]
                for member in members_without_history
            ]
        )
        history_by_channel_persona = {}
        for history in self.env["im_livechat.channel.member.history"].search_fetch(
            history_domain, ["channel_id", "guest_id", "member_id", "partner_id"]
        ):
            persona = history.partner_id or history.guest_id
            history_by_channel_persona[history.channel_id, persona] = history
        to_create = members_without_history.filtered(
            lambda m: (m.channel_id, m.partner_id or m.guest_id) not in history_by_channel_persona
        )
        self.env["im_livechat.channel.member.history"].create(
            [{"member_id": member.id, **values_by_member[member]} for member in to_create]
        )
        for member in self - to_create:
            persona = member.partner_id or member.guest_id
            history = (
                member.livechat_member_history_ids
                or history_by_channel_persona[member.channel_id, persona]
            )
            if history.member_id != member:
                values_by_member[member]["member_id"] = member.id
            if member in values_by_member:
                history.write(values_by_member[member])