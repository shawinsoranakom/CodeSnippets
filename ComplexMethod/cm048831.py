def test_cloud_storage_attachments(self):
        """Cloud attachments should be converted to links in outgoing emails."""

        thread_model = self.env["res.partner"].create({"name": "Cloud Test Partner", "email": "cloud@test.com"})
        cloud_attachment = self.env["ir.attachment"].create({
                "name": "cloud_attachment.txt",
                "type": "cloud_storage",
                "url": "https://storage.googleapis.com/fakebucket/cloud_attachment.txt",
                "res_model": "res.partner",
                "res_id": thread_model.id,
                "mimetype": "text/plain",
        })

        # A cloud attachment sent to a multiple partners -> attachment should be included as link in each
        partners = self.env["res.partner"].create([
                {"name": "Partner A", "email": "a@test.com"},
                {"name": "Partner B", "email": "b@test.com"},
        ])
        composer_form = Form(self.env["mail.compose.message"].with_context(
            default_model="res.partner",
            default_res_ids=thread_model.ids,
            default_composition_mode="comment",
            default_force_send=True,
            default_partner_ids=partners.ids,
        ))
        composer_form.attachment_ids.add(cloud_attachment)
        composer = composer_form.save()

        with self.mock_mail_gateway(mail_unlink_sent=False):
            composer._action_send_mail()
        self.assertEqual(len(self._mails), 2, "Two emails should be sent.")

        for body, attachment in zip([m["body"] for m in self._mails], self._new_mails.attachment_ids):
            large_attachment_link = str(self.env["ir.qweb"]._render("mail.mail_attachment_links", {"attachments": attachment}))
            self.assertEqual(body.count(large_attachment_link), 1,
                    "Sending mail with cloud_storage attachment should rendered it as a link in the outgoing email.",
            )

        # A cloud attachment and small txt attachment sent -> 1st should become a link, 2nd should be sent with the message
        small_attachment = self.env["ir.attachment"].create({
            "name": "Small attachment that should be attached normally.txt",
            "datas": base64.b64encode(b"tiny file").decode(),
            "mimetype": "text/plain",
            "res_model": "res.partner",
            "res_id": thread_model.id,
        })

        composer_form = Form(self.env['mail.compose.message'].with_context(
            default_model='res.partner',
            default_res_ids=thread_model.ids,
            default_composition_mode='comment',
            default_force_send=True,
            default_partner_ids=partners.ids,
        ))
        composer_form.attachment_ids.add(small_attachment)
        composer_form.attachment_ids.add(cloud_attachment)
        composer = composer_form.save()

        with self.mock_mail_gateway(mail_unlink_sent=False):
            composer._action_send_mail()

        self.assertEqual(len(self._mails), 2)
        body = self._mails[0]['body']
        for mail in self._mails:
            self.assertEqual(len(mail['attachments']), 1,
                "There should be only one small attachment per message")
            self.assertIn(small_attachment.name, str(mail['attachments']),
                "Only text attachment should be sent in the message")

        for body, attachment in zip([m["body"] for m in self._mails], self._new_mails.attachment_ids):
            large_attachment_link = str(self.env["ir.qweb"]._render("mail.mail_attachment_links", {"attachments": cloud_attachment}))
            self.assertEqual(body.count(large_attachment_link), 1,
                    "Sending mail with cloud_storage attachment should rendered it as a link in the outgoing email.",
            )

        # A large txt attachment and 2 cloud attachments sent -> All 3 shall became links
        cloud_attachment2 = self.env["ir.attachment"].create({
            "name": "cloud2 attachment also should be attached as a link",
            "type": "cloud_storage",
            "url": "https://storage.googleapis.com/fakebucket/cloud2.txt",
            "res_model": "res.partner",
            "res_id": thread_model.id,
        })

        max_email_size_bytes = self.env['ir.mail_server'].sudo()._get_max_email_size() * 1024 * 1024
        too_much_bytes = b"x" * (int(max_email_size_bytes) + 1)
        large_attachment = self.env["ir.attachment"].create({
            "name": "persistent large attachment should be attached as a link",
            "datas": base64.b64encode(too_much_bytes).decode(),
            "mimetype": "text/plain",
            "res_model": "res.partner",
            "res_id": thread_model.id,
        })
        composer_form = Form(self.env['mail.compose.message'].with_context(
            default_model='res.partner',
            default_res_ids=thread_model.ids,
            default_composition_mode='comment',
            default_force_send=True,
            default_partner_ids=partners.ids,
        ))
        composer_form.attachment_ids.add(large_attachment)
        composer_form.attachment_ids.add(cloud_attachment)
        composer_form.attachment_ids.add(cloud_attachment2)
        composer = composer_form.save()

        with self.mock_mail_gateway(mail_unlink_sent=False):
            composer._action_send_mail()

        for body, attachment in zip([m["body"] for m in self._mails], self._new_mails.attachment_ids):
            cloud_attachment_present = body.count(cloud_attachment.access_token) == body.count(cloud_attachment.name) == 1
            cloud_attachment2_present = body.count(cloud_attachment2.access_token) == body.count(cloud_attachment2.name) == 1
            large_attachment_link = str(self.env["ir.qweb"]._render("mail.mail_attachment_links", {"attachments": large_attachment}))
            self.assertTrue(body.count(large_attachment_link) == 1 and cloud_attachment_present and cloud_attachment2_present,
                "Two cloud and one large attachments should be converted and sent as links in the outgoing email.",
            )