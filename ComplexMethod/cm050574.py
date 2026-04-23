def test_mail_completed(self):
        """ When the slide.channel is completed, an email is supposed to be sent to people that completed it. """
        channel_2 = self.env['slide.channel'].create({
            'name': 'Test Course 2',
            'slide_ids': [(0, 0, {
                'name': 'Test Slide 1'
            })]
        })
        all_users = self.user_officer | self.user_emp | self.user_portal
        all_channels = self.channel | channel_2
        all_channels.sudo()._action_add_members(all_users.partner_id)
        slide_slide_vals = []
        for slide in all_channels.slide_content_ids:
            for user in self.user_officer | self.user_emp:
                slide_slide_vals.append({
                    'slide_id': slide.id,
                    'channel_id': self.channel.id,
                    'partner_id': user.partner_id.id,
                    'completed': True
                })
        self.env['slide.slide.partner'].create(slide_slide_vals)
        created_mails = self.env['mail.mail'].search([])

        # 2 'congratulations' emails are supposed to be sent to user_officer and user_emp
        for user in self.user_officer | self.user_emp:
            self.assertTrue(
                any(mail.model == 'slide.channel.partner' and user.partner_id in mail.recipient_ids
                    for mail in created_mails)
            )
        # user_portal has not completed the course, they should not receive anything
        self.assertFalse(
            any(mail.model == 'slide.channel.partner' and self.user_portal.partner_id in mail.recipient_ids
                for mail in created_mails)
        )