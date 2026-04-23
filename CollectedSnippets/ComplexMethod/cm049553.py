def _compute_question_ids(self):
        """ Update event questions from its event type. Depends are set only on
        event_type_id itself to emulate an onchange. Changing event type content
        itself should not trigger this method.

        When synchronizing questions:

          * lines with no registered answers for the event are removed;
          * type lines are added;
        """
        for event in self:
            questions_tokeep_ids = []
            if self._origin.question_ids:
                # Keep questions with attendee answers for the event.
                questions_tokeep_ids.extend(
                    (event.registration_ids.registration_answer_ids.question_id & self._origin.question_ids).ids
                )

            if not event.event_type_id and not questions_tokeep_ids:
                event.question_ids = self._default_question_ids()
                continue

            if questions_tokeep_ids:
                questions_toremove = event._origin.question_ids.filtered(
                    lambda question: question.id not in questions_tokeep_ids)
                command = [(3, question.id) for question in questions_toremove]
            else:
                command = [(5, 0)]
            event.question_ids = command
            event.question_ids = [Command.link(question_id.id) for question_id in event.event_type_id.question_ids]