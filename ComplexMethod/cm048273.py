def _compute_member_fields(self):
        for history in self:
            history.channel_id = history.channel_id or history.member_id.channel_id
            history.guest_id = history.guest_id or history.member_id.guest_id
            history.partner_id = history.partner_id or history.member_id.partner_id
            history.livechat_member_type = (
                history.livechat_member_type or history.member_id.livechat_member_type
            )
            history.chatbot_script_id = history.chatbot_script_id or history.member_id.chatbot_script_id
            history.agent_expertise_ids = (
                history.agent_expertise_ids or history.member_id.agent_expertise_ids
            )