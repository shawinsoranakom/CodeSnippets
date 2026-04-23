def _redirect_with_error(self, access_data, error_key):
        survey_sudo = access_data['survey_sudo']
        answer_sudo = access_data['answer_sudo']

        if error_key == 'survey_void' and access_data['can_answer']:
            return request.render("survey.survey_void_content", {'survey': survey_sudo, 'answer': answer_sudo})
        elif error_key == 'survey_closed' and access_data['can_answer']:
            return request.render("survey.survey_closed_expired", {'survey': survey_sudo})
        elif error_key == 'survey_auth':
            if not answer_sudo:  # survey is not even started
                redirect_url = '/web/login?redirect=/survey/start/%s' % survey_sudo.access_token
            elif answer_sudo.access_token:  # survey is started but user is not logged in anymore.
                if answer_sudo.partner_id and (answer_sudo.partner_id.user_ids or survey_sudo.users_can_signup):
                    if answer_sudo.partner_id.user_ids:
                        answer_sudo.partner_id.signup_cancel()
                    else:
                        answer_sudo.partner_id.signup_prepare()
                    redirect_url = answer_sudo.partner_id._get_signup_url_for_action(url='/survey/start/%s?answer_token=%s' % (survey_sudo.access_token, answer_sudo.access_token))[answer_sudo.partner_id.id]
                else:
                    redirect_url = '/web/login?redirect=%s' % ('/survey/start/%s?answer_token=%s' % (survey_sudo.access_token, answer_sudo.access_token))
            return request.render("survey.survey_auth_required", {'survey': survey_sudo, 'redirect_url': redirect_url})
        elif error_key == 'answer_deadline' and answer_sudo.access_token:
            return request.render("survey.survey_closed_expired", {'survey': survey_sudo})
        elif error_key in ['answer_wrong_user', 'token_wrong']:
            return request.render("survey.survey_access_error", {'survey': survey_sudo})

        return request.redirect("/")