def _action_unfollow(self, partner=None, guest=None, post_leave_message=True):
        self.ensure_one()
        if partner is None:
            partner = self.env["res.partner"]
        if guest is None:
            guest = self.env["mail.guest"]
        self.message_unsubscribe(partner.ids)
        member = self.env["discuss.channel.member"].search(
            [
                ("channel_id", "=", self.id),
                ("partner_id", "=", partner.id) if partner else ("guest_id", "=", guest.id),
            ]
        )
        custom_store = Store(bus_channel=member._bus_channel() or partner.main_user_id or guest)
        custom_store.add(self, {"close_chat_window": True, "isLocallyPinned": False}).bus_send()
        if not member:
            return
        if self.channel_type != "channel" and post_leave_message:
            notification = Markup('<div class="o_mail_notification" data-oe-type="channel-left">%s</div>') % _(
                "left the channel"
            )
            # sudo: mail.message - post as sudo since the user just unsubscribed from the channel
            member.channel_id.sudo().message_post(
                body=notification, subtype_xmlid="mail.mt_comment", author_id=partner.id
            )
        member.unlink()
        Store(bus_channel=self).add(
            self,
            [
                Store.Many("channel_member_ids", [], mode="DELETE", value=member),
                "member_count",
            ],
        ).bus_send()