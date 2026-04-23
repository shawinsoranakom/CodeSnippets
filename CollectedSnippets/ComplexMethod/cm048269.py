def get_session(self, channel_id, previous_operator_id=None, chatbot_script_id=None, persisted=True, **kwargs):
        channel = request.env["discuss.channel"]
        country = request.env["res.country"]
        guest = request.env["mail.guest"]
        store = Store()
        livechat_channel = (
            request.env["im_livechat.channel"]
            .with_context(lang=False)
            .sudo()
            .search([("id", "=", channel_id)])
        )
        if not livechat_channel:
            raise NotFound()
        if not request.env.user._is_public():
            country = request.env.user.country_id
        elif request.geoip.country_code:
            country = request.env["res.country"].search(
                [("code", "=", request.geoip.country_code)], limit=1
            )
        operator_info = livechat_channel._get_operator_info(
            previous_operator_id=previous_operator_id,
            chatbot_script_id=chatbot_script_id,
            country_id=country.id,
            lang=request.cookies.get("frontend_lang"),
            **kwargs
        )
        if not operator_info['operator_partner']:
            return False

        chatbot_script = operator_info['chatbot_script']
        is_chatbot_script = operator_info['operator_model'] == 'chatbot.script'
        non_persisted_channel_params, persisted_channel_params = self._process_extra_channel_params(**kwargs)

        if not persisted:
            channel_id = -1  # only one temporary thread at a time, id does not matter.
            chatbot_data = None
            if is_chatbot_script:
                welcome_steps = chatbot_script._get_welcome_steps()
                chatbot_data = {
                    "script": chatbot_script.id,
                    "steps": welcome_steps.mapped(lambda s: {"scriptStep": s.id}),
                }
                store.add(chatbot_script)
                store.add(welcome_steps)
            channel_info = {
                "fetchChannelInfoState": "fetched",
                "id": channel_id,
                "isLoaded": True,
                "livechat_operator_id": Store.One(
                    operator_info["operator_partner"], self.env["discuss.channel"]._store_livechat_operator_id_fields(),
                ),
                "scrollUnread": False,
                "channel_type": "livechat",
                "chatbot": chatbot_data,
                **non_persisted_channel_params,
            }
            store.add_model_values("discuss.channel", channel_info)
        else:
            if request.env.user._is_public():
                guest = guest.sudo()._get_or_create_guest(
                    guest_name=self._get_guest_name(),
                    country_code=request.geoip.country_code,
                    timezone=request.env["mail.guest"]._get_timezone_from_request(request),
                )
                livechat_channel = livechat_channel.with_context(guest=guest)
                request.update_context(guest=guest)
            channel_vals = livechat_channel._get_livechat_discuss_channel_vals(**operator_info)
            channel_vals.update(**persisted_channel_params)
            lang = request.env["res.lang"].search(
                [("code", "=", request.cookies.get("frontend_lang"))]
            )
            channel_vals.update({"country_id": country.id, "livechat_lang_id": lang.id})
            channel = request.env['discuss.channel'].with_context(
                lang=request.env['chatbot.script']._get_chatbot_language()
            ).sudo().create(channel_vals)
            channel_id = channel.id
            if is_chatbot_script:
                chatbot_script._post_welcome_steps(channel)
            if not is_chatbot_script or chatbot_script.operator_partner_id != channel.livechat_operator_id:
                channel._broadcast([channel.livechat_operator_id.id])
            if guest:
                store.add_global_values(guest_token=guest.sudo()._format_auth_cookie())
        request.env["res.users"]._init_store_data(store)
        # Make sure not to send "isLoaded" value on the guest bus, otherwise it
        # could be overwritten.
        if channel:
             store.add(
                 channel,
                 extra_fields={
                     "isLoaded": not is_chatbot_script,
                     "scrollUnread": False,
                 },
             )
        if not request.env.user._is_public():
            store.add(
                request.env.user.partner_id,
                {"email": request.env.user.partner_id.email},
            )
        return {
            "store_data": store.get_result(),
            "channel_id": channel_id,
        }