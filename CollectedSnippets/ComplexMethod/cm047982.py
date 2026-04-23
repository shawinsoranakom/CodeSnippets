def _message_post(self, *args, **kwargs):
                message = _message_post.origin(self, *args, **kwargs)
                # Don't execute automations for a message emitted during
                # the run of automations for a real message
                # Don't execute if we know already that a message is only internal
                message_sudo = message.sudo().with_context(active_test=False)
                if "__action_done"  in self.env.context or message_sudo.is_internal or message_sudo.subtype_id.internal:
                    return message
                if message_sudo.message_type in ('notification', 'auto_comment', 'user_notification'):
                    return message

                # always execute actions when the author is a customer
                # if author is not set, it means the message is coming from outside
                mail_trigger = "on_message_received" if not message_sudo.author_id or message_sudo.author_id.partner_share else "on_message_sent"
                automations = self.env['base.automation']._get_actions(self, [mail_trigger])
                for automation in automations.with_context(old_values=None):
                    records = automation._filter_pre(self, feedback=True)
                    _logger.debug(
                        "Processing automation rule %s (#%s) on %s records (_message_post)",
                        automation.sudo().name, automation.sudo().id, len(records),
                    )
                    automation._process(records)

                return message