def _rtc_invite_members(self, member_ids=None):
        """ Sends invitations to join the RTC call to all connected members of the thread who are not already invited,
            if member_ids is set, only the specified ids will be invited.

            :param list member_ids: list of the partner ids to invite
        """
        self.ensure_one()
        members = self.env["discuss.channel.member"].search(
            self._get_rtc_invite_members_domain(member_ids)
        )
        if members:
            members.rtc_inviting_session_id = self.rtc_session_ids.id
            Store(bus_channel=self.channel_id).add(
                self.channel_id,
                {
                    "invited_member_ids": Store.Many(
                        members,
                        [
                            Store.One("channel_id", [], as_thread=True),
                            *self.env["discuss.channel.member"]._to_store_persona("avatar_card"),
                        ],
                        mode="ADD",
                    ),
                },
            ).bus_send()
            devices, private_key, public_key = self.channel_id._web_push_get_partners_parameters(members.partner_id.ids)
            if devices:
                if self.channel_id.channel_type != 'chat':
                    icon = f"/web/image/discuss.channel/{self.channel_id.id}/avatar_128"
                elif guest := self.env["mail.guest"]._get_guest_from_context():
                    icon = f"/web/image/mail.guest/{guest.id}/avatar_128"
                elif partner := self.env.user.partner_id:
                    icon = f"/web/image/res.partner/{partner.id}/avatar_128"
                languages = [partner.lang for partner in devices.partner_id]
                payload_by_lang = {}
                for lang in languages:
                    env_lang = self.with_context(lang=lang).env
                    payload_by_lang[lang] = {
                        "title": env_lang._("Incoming call"),
                        "options": {
                            "body": env_lang._("Conference: %s", self.channel_id.display_name),
                            "icon": icon,
                            "vibrate": [100, 50, 100],
                            "requireInteraction": True,
                            "tag": self.channel_id._get_call_notification_tag(),
                            "data": {
                                "type": PUSH_NOTIFICATION_TYPE.CALL,
                                "model": "discuss.channel",
                                "action": "mail.action_discuss",
                                "res_id": self.channel_id.id,
                            },
                            "actions": [
                                {
                                    "action": PUSH_NOTIFICATION_ACTION.DECLINE,
                                    "type": "button",
                                    "title": env_lang._("Decline"),
                                },
                                {
                                    "action": PUSH_NOTIFICATION_ACTION.ACCEPT,
                                    "type": "button",
                                    "title": env_lang._("Accept"),
                                },
                            ]
                        }
                    }
                self.channel_id._web_push_send_notification(devices, private_key, public_key, payload_by_lang=payload_by_lang)
        return members