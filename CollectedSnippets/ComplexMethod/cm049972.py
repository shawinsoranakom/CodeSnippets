def _extract_filters_data(self, survey, post):
        """ Extracts the filters from the URL to returns the related user_input_lines and
        the parameters used to render/remove the filters on the results page (search_filters).

        The matching user_input_lines are all the lines tied to the user inputs which respect
        the survey base domain and which have lines matching all the filters.
        For example, with the filter 'Where do you live?|Brussels', we need to display ALL the lines
        of the survey user inputs which have answered 'Brussels' to this question.

        :return (recordset, List[dict]): all matching user input lines, each search filter data
        """
        user_input_line_subdomains = []
        search_filters = []

        answer_by_column, user_input_lines_ids = self._get_filters_from_post(post)

        # Matrix, Multiple choice, Simple choice filters
        if answer_by_column:
            answer_ids, row_ids = [], []
            for answer_column_id, answer_row_ids in answer_by_column.items():
                answer_ids.append(answer_column_id)
                row_ids += answer_row_ids

            answers_and_rows = request.env['survey.question.answer'].browse(answer_ids+row_ids)
            # For performance, accessing 'a.matrix_question_id' caches all useful fields of the
            # answers and rows records, avoiding unnecessary queries.
            answers = answers_and_rows.filtered(lambda a: not a.matrix_question_id)

            for answer in answers:
                if not answer_by_column[answer.id]:
                    # Simple/Multiple choice
                    user_input_line_subdomains.append(answer._get_answer_matching_domain())
                    search_filters.append(self._prepare_search_filter_answer(answer))
                else:
                    # Matrix
                    for row_id in answer_by_column[answer.id]:
                        row = answers_and_rows.filtered(lambda answer_or_row: answer_or_row.id == row_id)
                        user_input_line_subdomains.append(answer._get_answer_matching_domain(row_id))
                        search_filters.append(self._prepare_search_filter_answer(answer, row))

        # Char_box, Text_box, Numerical_box, Date, Datetime filters
        if user_input_lines_ids:
            user_input_lines = request.env['survey.user_input.line'].browse(user_input_lines_ids)
            for input_line in user_input_lines:
                user_input_line_subdomains.append(input_line._get_answer_matching_domain())
                search_filters.append(self._prepare_search_filter_input_line(input_line))

        # Compute base domain
        user_input_domain = self._get_results_page_user_input_domain(survey, **post)

        # Add filters domain to the base domain
        if user_input_line_subdomains:
            all_required_lines_domains = [
                [('user_input_line_ids', 'in', request.env['survey.user_input.line'].sudo()._search(subdomain))]
                for subdomain in user_input_line_subdomains
            ]
            user_input_domain = Domain.AND([user_input_domain, *all_required_lines_domains])

        # Get the matching user input lines
        user_inputs_query = request.env['survey.user_input'].sudo()._search(user_input_domain)
        user_input_lines = request.env['survey.user_input.line'].search([('user_input_id', 'in', user_inputs_query)])

        return user_input_lines, search_filters