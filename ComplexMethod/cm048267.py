def livechat_conversation_update_tags(self, channel_id, tag_ids, method="ADD"):
        """Add or remove tags from a live chat conversation."""
        if not self.env["im_livechat.conversation.tag"].has_access("write"):
            raise NotFound()
        channel = request.env["discuss.channel"].search([("id", "=", channel_id)])
        if not channel:
            raise NotFound()
        # sudo: discuss.channel - internal users having the rights to read the conversation and to
        # write tags can update the tags
        if method == "ADD":
            channel.sudo().livechat_conversation_tag_ids = [
                Command.link(tag_id) for tag_id in tag_ids
            ]
        elif method == "DELETE":
            channel.sudo().livechat_conversation_tag_ids = [
                Command.unlink(tag_id) for tag_id in tag_ids
            ]
        if channel.livechat_status == "need_help":
            request.env.ref("im_livechat.im_livechat_group_user")._bus_send(
                "im_livechat.looking_for_help/tags",
                {
                    "channel_id": channel.id,
                    "tag_ids": channel.sudo().livechat_conversation_tag_ids.ids,
                },
                subchannel="LOOKING_FOR_HELP",
            )