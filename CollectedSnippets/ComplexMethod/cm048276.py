def _message_post_after_hook(self, message, msg_vals):
        """
        This method is called just before _notify_thread() method which is calling the _to_store()
        method. We need a 'chatbot.message' record before it happens to correctly display the message.
        It's created only if the mail channel is linked to a chatbot step. We also need to save the
        user answer if the current step is a question selection.
        """
        if self.chatbot_current_step_id and not self.livechat_agent_history_ids:
            selected_answer = (
                self.env["chatbot.script.answer"]
                .browse(self.env.context.get("selected_answer_id"))
                .exists()
            )
            if selected_answer and selected_answer in self.chatbot_current_step_id.answer_ids:
                # sudo - chatbot.message: finding the question message to update the user answer is allowed.
                question_msg = (
                    self.env["chatbot.message"]
                    .sudo()
                    .search(
                        [
                            ("discuss_channel_id", "=", self.id),
                            ("script_step_id", "=", self.chatbot_current_step_id.id),
                        ],
                        order="id DESC",
                        limit=1,
                    )
                )
                question_msg.user_script_answer_id = selected_answer
                question_msg.user_raw_script_answer_id = selected_answer.id
                if store := self.env.context.get("message_post_store"):
                    store.add(message).add(question_msg.mail_message_id)
                partner, guest = self.env["res.partner"]._get_current_persona()
                Store(bus_channel=partner or guest).add_model_values(
                    "ChatbotStep",
                    {
                        "id": (self.chatbot_current_step_id.id, question_msg.mail_message_id.id),
                        "scriptStep": self.chatbot_current_step_id.id,
                        "message": question_msg.mail_message_id.id,
                        "selectedAnswer": selected_answer.id,
                    },
                ).bus_send()

            self.env["chatbot.message"].sudo().create(
                {
                    "mail_message_id": message.id,
                    "discuss_channel_id": self.id,
                    "script_step_id": self.chatbot_current_step_id.id,
                }
            )

        author_history = self.env["im_livechat.channel.member.history"]
        # sudo - discuss.channel: accessing history to update its state is acceptable
        if message.author_id or message.author_guest_id:
            author_history = self.sudo().livechat_channel_member_history_ids.filtered(
                lambda h: h.partner_id == message.author_id
                if message.author_id
                else h.guest_id == message.author_guest_id
            )
        if author_history:
            if message.message_type not in ("notification", "user_notification"):
                author_history.message_count += 1
        if author_history.livechat_member_type == "agent" and not author_history.response_time_hour:
            author_history.response_time_hour = (
                fields.Datetime.now() - author_history.create_date
            ).total_seconds() / 3600
        if not self.livechat_end_dt and author_history.livechat_member_type == "agent":
            self.livechat_failure = "no_failure"
        # sudo: discuss.channel - accessing livechat_status in internal code is acceptable
        if (
            not self.livechat_end_dt
            and self.sudo().livechat_status == "waiting"
            and author_history.livechat_member_type == "visitor"
        ):
            # sudo: discuss.channel - writing livechat_status when a message is posted is acceptable
            self.sudo().livechat_status = "in_progress"
        return super()._message_post_after_hook(message, msg_vals)