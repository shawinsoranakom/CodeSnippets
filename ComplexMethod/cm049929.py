def _post_message(self, raise_exception=True):
        """ Post the scheduled messages.
            They are posted using their creator as user so that one can check that the creator has
            still post permission on the related record, and to allow for the attachments to be
            transferred to the messages (see _process_attachments_for_post in mail.thread)
            if raise_exception is set to False, the method will skip the posting of a message
            instead of raising an error, and send a notification to the author about the failure.
            This is useful when scheduled messages are sent from the _post_messages_cron.
        """
        notification_parameters_whitelist = self._notification_parameters_whitelist()
        auto_commit = not modules.module.current_test
        for scheduled_message in self:
            message_creator = scheduled_message.create_uid
            try:
                scheduled_message.with_user(message_creator)._check()
                message = self.env[scheduled_message.model].browse(scheduled_message.res_id).with_context(
                        clean_context(scheduled_message.send_context or {})
                    ).with_user(message_creator).message_post(
                    attachment_ids=list(scheduled_message.attachment_ids.ids),
                    author_id=scheduled_message.author_id.id,
                    subject=scheduled_message.subject,
                    body=scheduled_message.body,
                    partner_ids=list(scheduled_message.partner_ids.ids),
                    subtype_xmlid='mail.mt_note' if scheduled_message.is_note else 'mail.mt_comment',
                    **{k: v for k, v in json.loads(scheduled_message.notification_parameters or '{}').items() if k in notification_parameters_whitelist},
                )
                scheduled_message._message_created_hook(message)
                if auto_commit:
                    self.env.cr.commit()
            except Exception:
                if raise_exception:
                    raise
                _logger.info("Posting of scheduled message with ID %s failed", scheduled_message.id, exc_info=True)
                # notify user about the failure (send content as user might have lost access to the record)
                if auto_commit:
                    self.env.cr.rollback()
                try:
                    self.env['mail.thread'].message_notify(
                        partner_ids=[message_creator.partner_id.id],
                        subject=_("A scheduled message could not be sent"),
                        body=_("The message scheduled on %(model)s(%(id)s) with the following content could not be sent:%(original_message)s",
                            model=scheduled_message.model,
                            id=scheduled_message.res_id,
                            original_message=Markup("<br>-----<br>%s<br>-----<br>") % scheduled_message.body,
                        )
                    )
                    if auto_commit:
                        self.env.cr.commit()
                except Exception:
                    # in case even message_notify fails, make sure the failing scheduled message
                    # will be deleted
                    _logger.exception("The notification about the failed scheduled message could not be sent")
                    if auto_commit:
                        self.env.cr.rollback()
        self.unlink()