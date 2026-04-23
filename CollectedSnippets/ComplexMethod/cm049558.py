def _compute_event_mail_ids(self):
        """ Update event configuration from its event type. Depends are set only
        on event_type_id itself, not its sub fields. Purpose is to emulate an
        onchange: if event type is changed, update event configuration. Changing
        event type content itself should not trigger this method.

        When synchronizing mails:

          * lines that are not sent and have no registrations linked are remove;
          * type lines are added;
        """
        for event in self:
            if not event.event_type_id and not event.event_mail_ids:
                event.event_mail_ids = self._default_event_mail_ids()
                continue

            # lines to keep: those with already sent emails or registrations
            mails_to_remove = event.event_mail_ids.filtered(
                lambda mail: not(mail._origin.mail_done) and not(mail._origin.mail_registration_ids)
            )
            command = [Command.unlink(mail.id) for mail in mails_to_remove]

            # lines to add: those which do not have the exact copy available in lines to keep
            if event.event_type_id.event_type_mail_ids:
                mails_to_keep_vals = {frozendict(mail._prepare_event_mail_values()) for mail in event.event_mail_ids - mails_to_remove}
                for mail in event.event_type_id.event_type_mail_ids:
                    mail_values = frozendict(mail._prepare_event_mail_values())
                    if mail_values not in mails_to_keep_vals:
                        command.append(Command.create(mail_values))
            if command:
                event.event_mail_ids = command