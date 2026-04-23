def _check_complete_chatbot_flow_result(self):
        operator = self.chatbot_script.operator_partner_id
        livechat_discuss_channel = self.env['discuss.channel'].search([
            ('livechat_channel_id', '=', self.livechat_channel.id),
            ('chatbot_current_step_id.chatbot_script_id', '=', self.chatbot_script.id),
            ('message_ids', '!=', False),
        ])
        self.assertTrue(bool(livechat_discuss_channel))
        self.assertEqual(len(livechat_discuss_channel), 1)

        conversation_messages = livechat_discuss_channel.message_ids.sorted('id')
        operator_member = livechat_discuss_channel.channel_member_ids.filtered(
            lambda m: m.partner_id == self.operator.partner_id
        )

        expected_messages = [
            ("Hello! I'm a bot!", operator, False),
            ("I help lost visitors find their way.", operator, False),
            # next message would normally have 'self.step_dispatch_buy_software' as answer
            # but it's wiped when restarting the script
            ("How can I help you?", operator, False),
            ("I\'d like to buy the software", False, False),
            ("Can you give us your email please?", operator, False),
            ("No, you won't get my email!", False, False),
            ("'No, you won't get my email!' does not look like a valid email. Can you please try again?", operator, False),
            ("okfine@fakeemail.com", False, False),
            ("Your email is validated, thank you!", operator, False),
            ("Would you mind providing your website address?", operator, False),
            ("https://www.fakeaddress.com", False, False),
            ("Great, do you want to leave any feedback for us to improve?", operator, False),
            ("Yes, actually, I'm glad you asked!", False, False),
            ("I think it's outrageous that you ask for all my personal information!", False, False),
            ("I will be sure to take this to your manager!", False, False),
            ("Ok bye!", operator, False),
            ("Restarting conversation...", operator, False),
            ("Hello! I'm a bot!", operator, False),
            ("I help lost visitors find their way.", operator, False),
            ("How can I help you?", operator, False),
            ("Pricing Question", False, False),
            ("For any pricing question, feel free ton contact us at pricing@mycompany.com", operator, False),
            ("We will reach back to you as soon as we can!", operator, False),
            ("Would you mind providing your website address?", operator, False),
            ("no", False, False),
            ("Great, do you want to leave any feedback for us to improve?", operator, False),
            ("no, nothing so say", False, False),
            ("Ok bye!", operator, False),
            ("Restarting conversation...", operator, False),
            ("Hello! I'm a bot!", operator, False),
            ("I help lost visitors find their way.", operator, False),
            ("How can I help you?", operator, self.step_dispatch_operator),
            ("I want to speak with an operator", False, False),
            ("I will transfer you to a human.", operator, False),
            (
                'invited <a href="#" data-oe-model="res.partner" data-oe-id="'
                f'{operator_member.partner_id.id}">@El Deboulonnator</a> to the channel',
                self.chatbot_script.operator_partner_id,
                False,
            ),
        ]

        self.assertEqual(len(conversation_messages), len(expected_messages))
        # "invited" notification is not taken into account in unread counter contribution.
        self.assertEqual(len(conversation_messages) - 1, operator_member.message_unread_counter)

        # check that the whole conversation is correctly saved
        # including welcome steps: see chatbot.script#_post_welcome_steps
        for conversation_message, expected_message in zip(conversation_messages, expected_messages):
            [body, operator, user_script_answer_id] = expected_message

            self.assertIn(body, conversation_message.body)

            if operator:
                self.assertEqual(conversation_message.author_id, operator)
            else:
                self.assertNotEqual(conversation_message.author_id, operator)

            if user_script_answer_id:
                self.assertEqual(
                    user_script_answer_id,
                    self.env['chatbot.message'].search([
                        ('mail_message_id', '=', conversation_message.id)
                    ], limit=1).user_script_answer_id
                )
        # History should only include messages after the conversation restart.
        history = livechat_discuss_channel._get_channel_history()
        parts = []
        previous_message_author = None
        visitor_partner = (
            conversation_messages.author_id.filtered(lambda p: p != operator)
            or conversation_messages.author_guest_id
        )
        for body, operator, _ in expected_messages[-6:-1]:
            message_author = operator or visitor_partner
            if previous_message_author != message_author:
                parts.append(
                    Markup("<br/><strong>%s:</strong><br/>")
                    % (
                        (message_author.user_livechat_username if message_author._name == "res.partner" else None)
                        or message_author.name
                    ),
                )
            parts.append(Markup("%s<br/>") % html2plaintext(body))
            previous_message_author = message_author
        expected_history = Markup("").join(parts)
        self.assertEqual(history, expected_history)