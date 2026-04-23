def _fetch_next_step(self, selected_answer_ids):
        """ Fetch the next step depending on the user's selected answers.
            If a step contains multiple triggering answers from the same step the condition between
            them must be a 'OR'. If is contains multiple triggering answers from different steps the
            condition between them must be a 'AND'.

            e.g:

            STEP 1 : A B
            STEP 2 : C D
            STEP 3 : E
            STEP 4 ONLY IF A B C E

            Scenario 1 (A C E):

            A in (A B) -> OK
            C in (C)   -> OK
            E in (E)   -> OK

            -> OK

            Scenario 2 (B D E):

            B in (A B) -> OK
            D in (C)   -> NOK
            E in (E)   -> OK

            -> NOK
        """
        self.ensure_one()
        domain = Domain('chatbot_script_id', '=', self.chatbot_script_id.id) & Domain('sequence', '>', self.sequence)
        if selected_answer_ids:
            domain &= Domain('triggering_answer_ids', 'in', selected_answer_ids.ids + [False])
        steps = self.env['chatbot.script.step'].search(domain)
        for step in steps:
            if not step.triggering_answer_ids:
                return step
            answers_by_step = defaultdict(list)
            for answer in step.triggering_answer_ids:
                answers_by_step[answer.script_step_id.id].append(answer)
            if all(any(answer in step_triggering_answers for answer in selected_answer_ids)
                   for step_triggering_answers in answers_by_step.values()):
                return step
        return self.env['chatbot.script.step']