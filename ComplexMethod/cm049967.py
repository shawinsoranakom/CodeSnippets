def survey_start(self, survey_token, answer_token=None, email=False, **post):
        """ Start a survey by providing
         * a token linked to a survey;
         * a token linked to an answer or generate a new token if access is allowed;
        """
        # Get the current answer token from cookie
        answer_from_cookie = False
        if not answer_token:
            answer_token = request.cookies.get('survey_%s' % survey_token)
            answer_from_cookie = bool(answer_token)

        access_data = self._get_access_data(survey_token, answer_token, ensure_token=False)

        if answer_from_cookie and access_data['validity_code'] in ('answer_wrong_user', 'token_wrong'):
            # If the cookie had been generated for another user or does not correspond to any existing answer object
            # (probably because it has been deleted), ignore it and redo the check.
            # The cookie will be replaced by a legit value when resolving the URL, so we don't clean it further here.
            access_data = self._get_access_data(survey_token, None, ensure_token=False)

        if access_data['validity_code'] is not True:
            return self._redirect_with_error(access_data, access_data['validity_code'])

        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']
        if not answer_sudo:
            try:
                answer_sudo = survey_sudo._create_answer(user=request.env.user, email=email)
            except UserError:
                answer_sudo = False

        if not answer_sudo:
            try:
                survey_sudo.with_user(request.env.user).check_access('read')
            except:
                return request.redirect("/")
            else:
                return request.render("survey.survey_403_page", {'survey': survey_sudo})

        # When resuming survey, restore language  + always enforce that the language is supported by the survey
        lang = self._get_lang_with_fallback(answer_sudo.sudo(False))
        response = request.redirect(self.env['ir.http']._url_for(f'/survey/{survey_sudo.access_token}', lang.code))
        response.set_cookie(f'survey_{survey_sudo.access_token}', answer_sudo.access_token, max_age=60 * 60 * 24)
        return response