def _check_validity(self, survey_sudo, answer_sudo, answer_token, ensure_token=True, check_partner=True):
        """ Check survey is open and can be taken. This does not check for
        security rules, only functional / business rules. It returns a string key
        allowing further manipulation of validity issues

         * survey_wrong: survey does not exist;
         * survey_auth: authentication is required;
         * survey_closed: survey is closed and does not accept input anymore;
         * survey_void: survey is void and should not be taken;
         * token_wrong: given token not recognized;
         * token_required: no token given, but it is required to access the survey;
         * answer_deadline: token linked to an expired answer;

        :param ensure_token: whether user input existence based on given access token
          should be enforced or not, depending on the route requesting a token or
          allowing external world calls;

        :param check_partner: Whether we must check that the partner associated to the target
          answer corresponds to the active user.
        """
        if not survey_sudo:
            return 'survey_wrong'

        if answer_token and not answer_sudo:
            return 'token_wrong'

        if not answer_sudo and ensure_token:
            return 'token_required'
        if not answer_sudo and survey_sudo.access_mode == 'token':
            return 'token_required'

        if survey_sudo.users_login_required and request.env.user._is_public():
            return 'survey_auth'

        if not survey_sudo.active and (not answer_sudo or not answer_sudo.test_entry):
            return 'survey_closed'

        if (not survey_sudo.page_ids and survey_sudo.questions_layout == 'page_per_section') or not survey_sudo.question_ids:
            return 'survey_void'

        if answer_sudo and answer_sudo.deadline and answer_sudo.deadline < datetime.now():
            return 'answer_deadline'

        if answer_sudo and check_partner:
            if request.env.user._is_public() and answer_sudo.partner_id and not answer_token:
                # answers from public user should not have any partner_id; this indicates probably a cookie issue
                return 'answer_wrong_user'
            if not request.env.user._is_public() and answer_sudo.partner_id != request.env.user.partner_id:
                # partner mismatch, probably a cookie issue
                return 'answer_wrong_user'

        return True