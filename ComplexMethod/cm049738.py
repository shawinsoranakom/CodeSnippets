def _compute_authorship(self):
        """ Computation is coming either from template, either from context.
        When having a template with a value set, copy it (in batch mode) or
        render it (in monorecord comment mode) on the composer. Otherwise
        try to take current user's email. When removing the template, fallback
        on default thread behavior (which is current user's email).

        Author is not controllable from the template currently. We therefore
        try to synchronize it with the given email_from (in rendered mode to
        avoid trying to find partner based on qweb expressions), or fallback
        on current user. """
        Thread = self.env['mail.thread'].with_context(active_test=False)
        for composer in self:
            rendering_mode = composer.composition_mode == 'comment' and not composer.composition_batch
            updated_author_id = None

            # update email_from first as it is the main used field currently
            if composer.template_id.email_from:
                composer._set_value_from_template('email_from')
            # switch to a template without email_from -> fallback on current user as default
            elif composer.template_id:
                composer.email_from = self.env.user.email_formatted
            # removing template or void from -> fallback on current user as default
            elif not composer.template_id or not composer.email_from:
                if self.env.context.get('default_email_from'):
                    composer.email_from = self.env.context['default_email_from']
                else:
                    composer.email_from = self.env.user.email_formatted
                    updated_author_id = self.env.user.partner_id.id

            # Update author. When being in rendered mode: link with rendered
            # email_from or fallback on current user if email does not match.
            # When changing template in raw mode or resetting also fallback.
            if composer.email_from and rendering_mode and not updated_author_id:
                updated_author_id, _ = Thread._message_compute_author(
                    None, composer.email_from,
                )
                if not updated_author_id:
                    updated_author_id = self.env.user.partner_id.id
            if not rendering_mode or not composer.template_id:
                updated_author_id = self.env.user.partner_id.id

            if updated_author_id:
                composer.author_id = updated_author_id