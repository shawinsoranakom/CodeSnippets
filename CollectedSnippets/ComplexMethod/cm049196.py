def _check_organizer_validation(self, sender_user, partner_included):
        """ Check if the proposed event organizer can be set accordingly. """
        # Edge case: events created or updated from Microsoft should not check organizer validation.
        change_from_microsoft = self.env.context.get('dont_notify', False)
        if sender_user and sender_user != self.env.user and not change_from_microsoft:
            current_sync_status = self._check_microsoft_sync_status()
            sender_sync_status = self.with_user(sender_user)._check_microsoft_sync_status()
            if not sender_sync_status and current_sync_status:
                raise ValidationError(
                    _("For having a different organizer in your event, it is necessary that "
                      "the organizer have its Odoo Calendar synced with Outlook Calendar."))
            elif sender_sync_status and not partner_included:
                raise ValidationError(
                    _("It is necessary adding the proposed organizer as attendee before saving the event."))