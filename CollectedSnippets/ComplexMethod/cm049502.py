def action_send_chat_request(self):
        """ Send a chat request to website_visitor(s).
        This creates a chat_request and a discuss_channel with livechat active flag.
        But for the visitor to get the chat request, the operator still has to speak to the visitor.
        The visitor will receive the chat request the next time he navigates to a website page.
        (see _handle_webpage_dispatch for next step)"""
        # check if visitor is available
        unavailable_visitors_count = self.env["discuss.channel"].search_count(
            [("livechat_visitor_id", "in", self.ids), ("livechat_end_dt", "=", False)]
        )
        if unavailable_visitors_count:
            raise UserError(_('Recipients are not available. Please refresh the page to get latest visitors status.'))
        # check if user is available as operator
        for website in self.mapped('website_id'):
            if not website.channel_id:
                raise UserError(_('No Livechat Channel allows you to send a chat request for website %s.', website.name))
        self.website_id.channel_id.write({'user_ids': [(4, self.env.user.id)]})
        # Create chat_requests and linked discuss_channels
        discuss_channel_vals_list = []
        for visitor in self:
            operator = self.env.user
            country = visitor.country_id
            visitor_name = "Visitor #%d (%s)" % (visitor.id, country.name) if country else f"Visitor #{visitor.id}"
            members_to_add = [Command.link(operator.partner_id.id)]
            if visitor.partner_id:
                members_to_add.append(Command.link(visitor.partner_id.id))
            discuss_channel_vals_list.append({
                'channel_partner_ids': members_to_add,
                "is_pending_chat_request": True,
                'livechat_channel_id': visitor.website_id.channel_id.id,
                'livechat_operator_id': self.env.user.partner_id.id,
                'channel_type': 'livechat',
                'country_id': country.id,
                'name': ', '.join([visitor_name, operator.livechat_username if operator.livechat_username else operator.name]),
                'livechat_visitor_id': visitor.id,
            })
        discuss_channels = self.env['discuss.channel'].create(discuss_channel_vals_list)
        for channel in discuss_channels:
            if not channel.livechat_visitor_id.partner_id:
                # sudo: mail.guest - creating a guest in a dedicated channel created from livechat
                guest = self.env["mail.guest"].sudo().create(
                    {
                        "country_id": country.id,
                        "lang": get_lang(channel.env).code,
                        "name": _("Visitor #%d", channel.livechat_visitor_id.id),
                        "timezone": visitor.timezone,
                    }
                )
                channel._add_members(guests=guest, post_joined_message=False)
        # Open empty channel to allow the operator to start chatting with the visitor
        Store(bus_channel=self.env.user).add(
            discuss_channels,
            extra_fields={"open_chat_window": True},
        ).bus_send()