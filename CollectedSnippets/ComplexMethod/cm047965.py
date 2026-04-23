def _prepare_lead_values_from_user_input_lines(self):
        ''' This prepares dict-formatted lead values from user input lines. It formats
            lead description and get user's nickname and his email, if they're provided.
            To write the description (notes in CRM) in HTML format, there are 5 cases:
                - Suggested answers question: <li>Question — Answer 1, Answer 3</li>
                - Matrix question:  <li>
                                        Question
                                        <br/>&emsp;Line label 1 — Answer 1
                                        <br/>&emsp;Line label 1 — Answer 3
                                        <br/>&emsp;Line label 4 — Answer 2
                                    </li>
                - Long text question:   <li>
                                            Question
                                            <br/>&emsp;Text line 1
                                            <br/>&emsp;Text line 2
                                            <br/>&emsp;Text line 3
                                        </li>
                - Other types: <li>Question — Answer</li>
                - Skipped question: <li>Question — <i>Skipped</i></li>

            Note: '<br/>&emsp;' is used to get a line break with indentation
        '''
        self.ensure_one()

        answers_by_question = self.user_input_line_ids.grouped('question_id')
        html_input_lines = []
        line_break_indented_markuped = Markup('<br/>&emsp;')
        user_nickname = public_user_mail = ''
        for question, input_lines in answers_by_question.items():
            answers, last_row = [], ''
            # initial_indent is useful to manage matrix writing and multiple_answers for several suggested answers chosen
            initial_indent, multiple_answers = False, False
            # When no response is given, an input line is still created with the skipped field set to True.
            # However, if there is a comment (option for suggested answers question), another input line is
            # created with the comment (and skipped set to False).
            # In summary, the next recordset is empty when no response and no comment are left.
            input_lines_not_skipped = input_lines.filtered(lambda line: not line.skipped)
            if len(input_lines_not_skipped) == 0:
                answers = [Markup(' — <i>%(skipped)s</i>') % {'skipped': _('Skipped')}]
            for input_line_index, input_line in enumerate(input_lines_not_skipped):
                # Write description line according to the patterns explained above.
                # We usually write the question first, then the answer; but if we have several answers
                # for the same question, we continue the editing we have already started.
                # Note: Markup ensures the validity of HTML and we escape responses and labels that could
                # be a source of injection if applicable. Since the placeholder values are not in the Markup
                # constructor, this automatically escapes those fields.
                if question.question_type == 'char_box':
                    # Check if the question has a nickname recorded or an email answer
                    if not user_nickname and question.save_as_nickname:
                        user_nickname = input_line._get_answer_value()
                    if not public_user_mail and question.validation_email:
                        public_user_mail = input_line._get_answer_value()
                    answers.append(Markup(' %(separator)s %(answer)s') % {
                        'separator': '—',
                        'answer': input_line._get_answer_value(),
                    })

                elif question.question_type == 'matrix' and (row := input_line.matrix_row_id) and \
                    (col_value := input_line.suggested_answer_id.display_name) and (last_row != row):
                    initial_indent = True
                    last_row = row
                    answers.append(Markup('%(row_name)s — %(col_value)s') % {
                            'row_name': row.display_name,
                            'col_value': col_value,
                        })
                elif question.question_type == 'matrix' and row:  # For multiple suggested answers (complete last edition)
                    answers[-1] += Markup(', %(col_value)s') % {'col_value': col_value}
                elif question.question_type == 'matrix' and not row:  # Comment field
                    initial_indent = True
                    # Leave the placeholder values in the constructor to keep line break with indentation
                    answers.append(Markup('<i><b>%(comment)s</b></i> — %(comment_answer)s' % {
                        'comment': _('Comment'),
                        'comment_answer': escape(input_line._get_answer_value()).replace('\n', line_break_indented_markuped),
                        })
                    )

                elif question.question_type in ['numerical_box', 'scale', 'date', 'datetime']:
                    answers.append(Markup(' %(separator)s %(answer)s') % {
                        'separator': '—',
                        'answer': str(input_line._get_answer_value()),
                    })

                elif question.question_type in ['simple_choice', 'multiple_choice'] and input_line.answer_type == 'char_box':  # Comment case
                    answers.append(Markup('%(line_break_indented_markuped)s<i><b>%(comment)s</b></i> — %(answer)s') % {
                        'line_break_indented_markuped': line_break_indented_markuped if multiple_answers or len(input_lines_not_skipped) == 1 else '',
                        'comment': _('Comment'),
                        'answer': escape(str(input_line._get_answer_value())).replace('\n', line_break_indented_markuped),
                    })
                elif question.question_type in ['simple_choice', 'multiple_choice']:
                    multiple_answers = input_line_index != 0
                    answer = str(input_line._get_answer_value())
                    # For picture answers without label, we use the filename by the way
                    if input_line.suggested_answer_id and not input_line._get_answer_value():
                        answer = input_line.suggested_answer_id.value_image_filename or ''
                    answers.append(Markup('%(separator)s %(answer)s') % {
                        'separator': ' —' if not multiple_answers else ',',  # The "else" is useful for multiple suggested answers
                        'answer': answer,
                    })

                elif question.question_type == 'text_box':
                    # Leave the placeholder values in the constructor to keep line break with indentation
                    answers = ['', Markup('%(text)s' % {'text': escape(input_line._get_answer_value()).replace('\n', line_break_indented_markuped)})]  # '' for line break after with the next join

            # Leave the placeholder values in the constructor so as not to escape the pretty print
            html_input_lines.append(Markup('<li>%(question_title)s%(initial_indent)s%(user_inputs)s</li>') % {
                'question_title': escape(question.title),
                'initial_indent': line_break_indented_markuped if initial_indent else '',
                'user_inputs': Markup('').join(answers) if multiple_answers else line_break_indented_markuped.join(answers),
            })

        # Leave the placeholder values in the constructor so as not to escape the pretty print
        description = Markup('<div>%(answers)s:</div><ul>%(survey_answers)s</ul>') % {
            'answers': _('Answers'),
            'survey_answers': Markup('').join(html_input_lines),
        }
        return {
            'description': description,
            'user_nickname': user_nickname,
            'public_user_mail': public_user_mail,
        }