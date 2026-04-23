def _to_store(self, store: Store, fields):
        """Extends the channel header by adding the livechat operator and the 'anonymous' profile"""
        super()._to_store(store, [f for f in fields if f != "chatbot_current_step"])
        if "chatbot_current_step" not in fields:
            return
        lang = self.env["chatbot.script"]._get_chatbot_language()
        for channel in self.filtered(lambda channel: channel.chatbot_current_step_id):
            # sudo: chatbot.script.step - returning the current script/step of the channel
            current_step_sudo = channel.chatbot_current_step_id.sudo().with_context(lang=lang)
            chatbot_script = current_step_sudo.chatbot_script_id
            step_message = self.env["chatbot.message"]
            if not current_step_sudo.is_forward_operator:
                step_message = channel.sudo().chatbot_message_ids.filtered(
                    lambda m: m.script_step_id == current_step_sudo
                    and m.mail_message_id.author_id == chatbot_script.operator_partner_id
                )[:1]
            current_step = {
                "scriptStep": current_step_sudo.id,
                "message": step_message.mail_message_id.id,
                "operatorFound": current_step_sudo.is_forward_operator
                and channel.livechat_operator_id != chatbot_script.operator_partner_id,
            }
            store.add(current_step_sudo)
            store.add(chatbot_script)
            chatbot_data = {
                "script": chatbot_script.id,
                "steps": [current_step],
                "currentStep": current_step,
            }
            store.add(channel, {"chatbot": chatbot_data})