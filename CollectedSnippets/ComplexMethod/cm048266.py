def chatbot_trigger_step(self, channel_id, chatbot_script_id=None, data_id=None):
        chatbot_language = self.env["chatbot.script"]._get_chatbot_language()
        discuss_channel = request.env["discuss.channel"].with_context(lang=chatbot_language).search([("id", "=", channel_id)])
        if not discuss_channel:
            return None

        next_step = False
        # sudo: chatbot.script.step - visitor can access current step of the script
        if current_step := discuss_channel.sudo().chatbot_current_step_id:
            if (
                current_step.is_forward_operator
                and discuss_channel.livechat_operator_id
                != current_step.chatbot_script_id.operator_partner_id
            ):
                return None
            chatbot = current_step.chatbot_script_id
            domain = [
                ("author_id", "!=", chatbot.operator_partner_id.id),
                ("model", "=", "discuss.channel"),
                ("res_id", "=", channel_id),
            ]
            # sudo: mail.message - accessing last message to process answer is allowed
            user_answer = self.env["mail.message"].sudo().search(domain, order="id desc", limit=1)
            next_step = current_step._process_answer(discuss_channel, user_answer.body)
        elif chatbot_script_id:  # when restarting, we don't have a "current step" -> set "next" as first step of the script
            chatbot = request.env['chatbot.script'].sudo().browse(chatbot_script_id).with_context(lang=chatbot_language)
            if chatbot.exists():
                next_step = chatbot.script_step_ids[:1]
        partner, guest = self.env["res.partner"]._get_current_persona()
        store = Store(bus_channel=partner or guest)
        store.data_id = data_id
        if not next_step:
            # sudo - discuss.channel: marking the channel as closed as part of the chat bot flow
            discuss_channel.sudo().livechat_end_dt = fields.Datetime.now()
            step_message = next(
                # sudo - chatbot.message.id: visitor can access chat bot messages.
                m.mail_message_id for m in discuss_channel.sudo().chatbot_message_ids
                if m.script_step_id == current_step
                and m.mail_message_id.author_id == chatbot.operator_partner_id
            )
            store.add(discuss_channel)
            store.add_model_values(
                "ChatbotStep",
                {
                    "id": (current_step.id, step_message.id),
                    "scriptStep": current_step.id,
                    "message": step_message.id,
                    "isLast": True,
                },
            )
            store.resolve_data_request()
            store.bus_send()
            return store.get_result()
        # sudo: discuss.channel - updating current step on the channel is allowed
        discuss_channel.sudo().chatbot_current_step_id = next_step.id
        posted_message = next_step._process_step(discuss_channel)
        store.add(posted_message).add(next_step)
        store.resolve_data_request(
            chatbot_step={"scriptStep": next_step.id, "message": posted_message.id}
        )
        chatbot_next_step_id = (next_step.id, posted_message.id)
        store.add_model_values(
            "ChatbotStep",
            {
                "id": chatbot_next_step_id,
                "message": posted_message.id,
                "operatorFound": next_step.is_forward_operator
                and discuss_channel.livechat_operator_id != chatbot.operator_partner_id,
                "scriptStep": next_step.id,
            },
        )
        store.add_model_values(
            "Chatbot",
            {
                "currentStep": {
                    "id": chatbot_next_step_id,
                    "scriptStep": next_step.id,
                    "message": posted_message.id,
                },
                "id": (chatbot.id, discuss_channel.id),
                "script": chatbot.id,
                "thread": Store.One(discuss_channel, [], as_thread=True),
                "steps": [("ADD", [{
                    "scriptStep": chatbot_next_step_id[0],
                    "message": chatbot_next_step_id[1]
                }])],
            },
        )
        store.bus_send()