def _check_answer_creation(self, user, partner, email, test_entry=False, check_attempts=True, invite_token=False):
        """ Ensure conditions to create new tokens are met. """
        self.ensure_one()
        if test_entry:
            try:
                self.with_user(user).check_access('read')
            except AccessError:
                raise exceptions.UserError(_('Creating test token is not allowed for you.'))

        if not test_entry:
            if not self.active:
                raise exceptions.UserError(_('Creating token for closed/archived surveys is not allowed.'))
            if self.access_mode == 'authentication':
                # signup possible -> should have at least a partner to create an account
                if self.users_can_signup and not user and not partner:
                    raise exceptions.UserError(_('Creating token for external people is not allowed for surveys requesting authentication.'))
                # no signup possible -> should be a not public user (employee or portal users)
                if not self.users_can_signup and (not user or user._is_public()):
                    raise exceptions.UserError(_('Creating token for external people is not allowed for surveys requesting authentication.'))
            if self.access_mode == 'internal' and (not user or not user._is_internal()):
                raise exceptions.UserError(_('Creating token for anybody else than employees is not allowed for internal surveys.'))
            if check_attempts and not self._has_attempts_left(partner or (user and user.partner_id), email, invite_token):
                raise exceptions.UserError(_('No attempts left.'))