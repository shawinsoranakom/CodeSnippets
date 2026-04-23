def _prepare_survey_data(self, survey_sudo, answer_sudo, **post):
        """ This method prepares all the data needed for template rendering, in function of the survey user input state.
            :param post:
                - previous_page_id : come from the breadcrumb or the back button and force the next questions to load
                                     to be the previous ones.
                - next_skipped_page : force the display of next skipped question or page if any."""
        data = {
            'is_html_empty': is_html_empty,
            'survey': survey_sudo,
            'answer': answer_sudo,
            'skipped_questions': answer_sudo._get_skipped_questions(),
            'breadcrumb_pages': [{
                'id': page.id,
                'title': page.title,
            } for page in survey_sudo.page_ids],
            'format_datetime': lambda dt: format_datetime(request.env, dt, dt_format=False),
            'format_date': lambda date: format_date(request.env, date)
        }
        if answer_sudo.state == 'new':
            # Data for the language selector
            supported_lang_codes = survey_sudo._get_supported_lang_codes()
            data['languages'] = [(lang_code, self.env['res.lang']._get_data(code=lang_code)['name'])
                                 for lang_code in supported_lang_codes]
            data['lang_code'] = self._get_lang_with_fallback(answer_sudo.sudo(False)).code
        triggering_answers_by_question, triggered_questions_by_answer, selected_answers = answer_sudo._get_conditional_values()
        if survey_sudo.questions_layout != 'page_per_question':
            data.update({
                'triggering_answers_by_question': {
                    question.id: triggering_answers.ids
                    for question, triggering_answers in triggering_answers_by_question.items() if triggering_answers
                },
                'triggered_questions_by_answer': {
                    answer.id: triggered_questions.ids
                    for answer, triggered_questions in triggered_questions_by_answer.items()
                },
                'selected_answers': selected_answers.ids
            })

        if not answer_sudo.is_session_answer and survey_sudo.is_time_limited and answer_sudo.start_datetime:
            data.update({
                'server_time': fields.Datetime.now(),
                'timer_start': answer_sudo.start_datetime.isoformat(),
                'time_limit_minutes': survey_sudo.time_limit
            })

        page_or_question_key = 'question' if survey_sudo.questions_layout == 'page_per_question' else 'page'

        # Bypass all if page_id is specified (comes from breadcrumb or previous button)
        if 'previous_page_id' in post:
            previous_page_or_question_id = int(post['previous_page_id'])
            new_previous_id = survey_sudo._get_next_page_or_question(answer_sudo, previous_page_or_question_id, go_back=True).id
            page_or_question = request.env['survey.question'].sudo().browse(previous_page_or_question_id)
            data.update({
                page_or_question_key: page_or_question,
                'previous_page_id': new_previous_id,
                'has_answered': answer_sudo.user_input_line_ids.filtered(lambda line: line.question_id.id == new_previous_id),
                'can_go_back': survey_sudo._can_go_back(answer_sudo, page_or_question),
            })
            return data

        if answer_sudo.state == 'in_progress':
            next_page_or_question = None
            if answer_sudo.is_session_answer:
                next_page_or_question = survey_sudo.session_question_id
            else:
                if 'next_skipped_page' in post:
                    next_page_or_question = answer_sudo._get_next_skipped_page_or_question()
                if not next_page_or_question:
                    next_page_or_question = survey_sudo._get_next_page_or_question(
                        answer_sudo,
                        answer_sudo.last_displayed_page_id.id if answer_sudo.last_displayed_page_id else 0)
                    # fallback to skipped page so that there is a next_page_or_question otherwise this should be a submit
                    if not next_page_or_question:
                        next_page_or_question = answer_sudo._get_next_skipped_page_or_question()

                if next_page_or_question:
                    if answer_sudo.survey_first_submitted:
                        survey_last = answer_sudo._is_last_skipped_page_or_question(next_page_or_question)
                    else:
                        survey_last = survey_sudo._is_last_page_or_question(answer_sudo, next_page_or_question)
                    values = {'survey_last': survey_last}
                    # On the last survey page, get the suggested answers which are triggering questions on the following pages
                    # to dynamically update the survey button to "submit" or "continue" depending on the selected answers.
                    # NB: Not in the skipped questions flow as conditionals aren't handled.
                    if not answer_sudo.survey_first_submitted and survey_last and survey_sudo.questions_layout != 'one_page':
                        pages_or_questions = survey_sudo._get_pages_or_questions(answer_sudo)
                        following_questions = pages_or_questions.filtered(lambda page_or_question: page_or_question.sequence > next_page_or_question.sequence)
                        next_page_questions_suggested_answers = next_page_or_question.suggested_answer_ids
                        if survey_sudo.questions_layout == 'page_per_section':
                            following_questions = following_questions.question_ids
                            next_page_questions_suggested_answers = next_page_or_question.question_ids.suggested_answer_ids
                        values['survey_last_triggering_answers'] = [
                            answer.id for answer in triggered_questions_by_answer
                            if answer in next_page_questions_suggested_answers and any(q in following_questions for q in triggered_questions_by_answer[answer])
                        ]
                    data.update(values)

            if answer_sudo.is_session_answer and next_page_or_question.is_time_limited:
                data.update({
                    'timer_start': survey_sudo.session_question_start_time.isoformat(),
                    'time_limit_minutes': next_page_or_question.time_limit / 60
                })

            data.update({
                page_or_question_key: next_page_or_question,
                'has_answered': answer_sudo.user_input_line_ids.filtered(lambda line: line.question_id == next_page_or_question),
                'can_go_back': survey_sudo._can_go_back(answer_sudo, next_page_or_question),
            })
            if survey_sudo.questions_layout != 'one_page':
                data.update({
                    'previous_page_id': survey_sudo._get_next_page_or_question(answer_sudo, next_page_or_question.id, go_back=True).id
                })
        elif answer_sudo.state == 'done' or answer_sudo.survey_time_limit_reached:
            # Display success message
            return self._prepare_survey_finished_values(survey_sudo, answer_sudo)

        return data