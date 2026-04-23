def send_email_reminder(self, track_id, email_to):
        """ Send email, to email_to if the user is public otherwise to the user email address,
        with tracks' reminders for external calendars. """
        template = self.env.ref("website_event_track.mail_template_data_track_reminder", raise_if_not_found=False)
        if not template:
            return {'success': False, 'error': 'missing_template'}

        track_su = self.env['event.track'].sudo().browse(track_id)
        # Check that the visitor has the permission to read the track on the website.
        track = track_su.filtered_domain(self._get_event_tracks_domain(track_su.event_id))
        valid_email_to = tools.email_normalize(email_to if request.env.user._is_public() else request.env.user.email)
        error_message = ''
        if not track:
            error_message = _('Invalid data.')
        elif not valid_email_to:
            error_message = _('Invalid email.')
        elif track.is_track_done or track.event_id.is_finished:
            error_message = _('The talk is already finished.')
        elif not track.is_track_upcoming:
            error_message = _('The talk has already begun.')
        if error_message:
            return {'success': False, 'message': error_message}

        template.sudo().with_context(
            lang=request.cookies.get('frontend_lang') if request.env.user._is_public() else request.env.context.get('lang', request.env.user.lang)
        ).send_mail(track.id, email_values={'email_to': valid_email_to})
        return {'success': True}