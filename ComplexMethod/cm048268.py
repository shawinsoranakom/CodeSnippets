def _process_request_for_all(self, store: Store, name, params):
        super()._process_request_for_all(store, name, params)
        if name == "init_livechat":
            partner, guest = request.env["res.partner"]._get_current_persona()
            if partner:
                store.add_global_values(self_partner=Store.One(partner, extra_fields="email"))
            if guest:
                store.add_global_values(self_guest=Store.One(guest))
            # sudo - im_livechat.channel: allow access to live chat channel to
            # check if operators are available.
            channel = request.env["im_livechat.channel"].sudo().search([("id", "=", params)])
            if not channel:
                return
            country_id = (
                # sudo - res.country: accessing user country is allowed.
                request.env["res.country"].sudo().search([("code", "=", code)]).id
                if (code := request.geoip.country_code)
                else None
            )
            url = request.httprequest.headers.get("Referer")
            if (
                # sudo - im_livechat.channel.rule: getting channel's rule is allowed.
                matching_rule := request.env["im_livechat.channel.rule"]
                .sudo()
                .match_rule(params, url, country_id)
            ):
                matching_rule = matching_rule.with_context(
                    lang=request.env["chatbot.script"]._get_chatbot_language(),
                )
                store.add_global_values(livechat_rule=Store.One(matching_rule))
            store.add_global_values(
                livechat_available=matching_rule.action != "hide_button"
                and bool(matching_rule._is_bot_configured() or channel.available_operator_ids),
                can_download_transcript=bool(
                    request.env.ref("im_livechat.action_report_livechat_conversation", False),
                ),
            )