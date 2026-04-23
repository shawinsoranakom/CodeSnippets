def test_routing_reply_mailing_references(self):
        """ Test mass mailing emails when providers rewrite messageID: references
        should allow to find the original message. """
        # send mailing on records using composer, in both reply and force new modes
        for reply_to_mode, auto_delete_keep_log in [
            ('new', True),
            ('update', True),
            ('new', False),  # reference is lost, but reply alias should be ok
            ('update', False),  # reference is lost, hence considered as a reply to catchall, is going to crash (FIXME ?)
        ]:
            with self.subTest(reply_to_mode=reply_to_mode, auto_delete_keep_log=auto_delete_keep_log), self.mock_mail_gateway(mail_unlink_sent=True):
                composer_form = Form(self.env['mail.compose.message'].with_context({
                    'active_ids': self.test_records.ids,
                    'default_auto_delete': True,
                    'default_auto_delete_keep_log': auto_delete_keep_log,
                    'default_composition_mode': 'mass_mail',
                    'default_email_from': self.user_employee.email_formatted,
                    'default_model': self.test_records._name,
                    'default_subject': 'Coucou Hibou',
                }))
                composer_form.body = f'<p>Hello <t t-out="object.name"/></p>'
                composer_form.reply_to_mode = reply_to_mode
                if reply_to_mode == 'new':
                    composer_form.reply_to = self.alias.display_name
                composer = composer_form.save()
                mails, _msg = composer._action_send_mail()
                self.assertFalse(mails.exists())

                # check reply using references
                # TDE TODO: update tooling
                outgoing_message_ids = [outgoing['message_id'] for outgoing in self._mails]
                self.assertEqual(len(set(outgoing_message_ids)), len(self.test_records),
                                'All message IDs should be different')
                for record in self.test_records:
                    outgoing = self._find_sent_email(self.user_employee.email_formatted, [record.email_from])
                    # for some reason, provider rewrites message_id, then customer replies
                    outgoing['message_id'] = f'<ILikeToRewriteMessageIDFor{record.id}-{record._name}@zboing>'
                    extra = f'In-Reply-To:{outgoing["message_id"]}\nReferences:{outgoing["message_id"]} {outgoing["references"]}\n'
                    with RecordCapturer(self.env['mail.message']) as capture_messages:
                        gateway_record = self.format_and_process(
                            MAIL_TEMPLATE, outgoing['email_to'][0], outgoing['reply_to'],
                            extra=extra,
                            subject=f'Re: {outgoing["subject"]} - from {outgoing["email_to"][0]} ({reply_to_mode} {auto_delete_keep_log})',
                            debug_log=False,
                        )
                    new_message = capture_messages.records
                    # as outgoing mail is unlinked with its mail.message -> cannot find parent -> bounce
                    if reply_to_mode == 'update' and not auto_delete_keep_log:
                        self.assertFalse(new_message)
                        self.assertFalse(gateway_record)
                        continue
                    self.assertTrue(new_message)
                    if reply_to_mode == 'update':
                        self.assertFalse(gateway_record, 'No record created based on subject, as it replies to the thread')
                        self.assertMessageFields(new_message, {
                            'email_from': record.email_from,
                            'model': record._name,
                            'res_id': record.id,
                        })
                    else:
                        self.assertNotEqual(gateway_record, record)
                        self.assertMessageFields(new_message, {
                            'email_from': record.email_from,
                            'model': gateway_record._name,
                            'res_id': gateway_record.id,
                        })