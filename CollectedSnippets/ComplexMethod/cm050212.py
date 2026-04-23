def test_notify_by_push_channel(self, push_to_end_point):
        """ Test various use case with discuss.channel. Chat and group channels
        sends push notifications, channel not. """
        chat_channel, channel_channel, group_channel = self.env['discuss.channel'].with_user(self.user_email).create([
            {
                'channel_partner_ids': [
                    (4, self.user_email.partner_id.id),
                    (4, self.user_inbox.partner_id.id),
                ],
                'channel_type': channel_type,
                'name': f'{channel_type} Message' if channel_type != 'group' else '',
            } for channel_type in ['chat', 'channel', 'group']
        ])
        group_channel._add_members(guests=self.guest)

        for channel, sender, notification_count in zip(
            (chat_channel + channel_channel + group_channel + group_channel),
            (self.user_email, self.user_email, self.user_email, self.guest),
            (1, 0, 1, 2),
        ):
            with self.subTest(channel_type=channel.channel_type):
                if sender == self.guest:
                    channel_as_sender = channel.with_user(self.env.ref('base.public_user')).with_context(guest=sender)
                else:
                    channel_as_sender = channel.with_user(self.user_email)
                # sudo: discuss.channel - guest can post as sudo in a test (simulating RPC without using network)
                channel_as_sender.sudo().message_post(
                        body='Test Push',
                        message_type='comment',
                        subtype_xmlid='mail.mt_comment',
                    )
                self.assertEqual(push_to_end_point.call_count, notification_count)
                if notification_count > 0:
                    payload_value = json.loads(push_to_end_point.call_args.kwargs['payload'])
                    if channel.channel_type == 'chat':
                        self.assertEqual(payload_value['title'], f'{self.user_email.name}')
                    elif channel.channel_type == 'group':
                        self.assertIn(self.user_email.name, payload_value['title'])
                        self.assertIn(self.user_inbox.name, payload_value['title'])
                        self.assertIn(self.guest.name, payload_value['title'])
                        self.assertNotIn("False", payload_value['title'])
                    else:
                        self.assertEqual(payload_value['title'], f'#{channel.name}')
                    icon = (
                        '/web/static/img/odoo-icon-192x192.png'
                        if sender == self.guest
                        else f'/web/image/res.partner/{self.user_email.partner_id.id}/avatar_128'
                    )
                    self.assertEqual(payload_value['options']['icon'], icon)
                    self.assertEqual(payload_value['options']['body'], 'Test Push')
                    self.assertEqual(payload_value['options']['data']['res_id'], channel.id)
                    self.assertEqual(payload_value['options']['data']['model'], channel._name)
                    self.assertEqual(push_to_end_point.call_args.kwargs['device']['endpoint'], 'https://test.odoo.com/webpush/user2')
                push_to_end_point.reset_mock()

        # Test Direct Message with channel muted -> should skip push notif
        now = datetime.now()
        self.env['discuss.channel.member'].search([
            ('partner_id', 'in', (self.user_email.partner_id + self.user_inbox.partner_id).ids),
            ('channel_id', 'in', (chat_channel + channel_channel + group_channel).ids),
        ]).write({
            'mute_until_dt': now + timedelta(days=5)
        })
        chat_channel.with_user(self.user_email).message_post(
            body='Test',
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )
        push_to_end_point.assert_not_called()
        push_to_end_point.reset_mock()

        self.env["discuss.channel.member"].search([
            ("partner_id", "in", (self.user_email.partner_id + self.user_inbox.partner_id).ids),
            ("channel_id", "in", (chat_channel + channel_channel + group_channel).ids),
        ]).write({
            "mute_until_dt": False,
        })

        # Test Channel Message
        group_channel.with_user(self.user_email).message_post(
            body='Test',
            partner_ids=self.user_inbox.partner_id.ids,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )
        push_to_end_point.assert_called_once()