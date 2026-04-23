def copy(self, default=None):
        """Correctly copy the 'triggering_answer_ids' field from the original to the clone.

        This needs to be done in post-processing to make sure we get references to the newly
        created answers from the copy instead of references to the answers of the original.
        This implementation assumes that the order of created answers will be kept between
        the original and the clone, using 'zip()' to match the records between the two.

        Note that when `question_ids` is provided in the default parameter, it falls back to the
        standard copy, meaning that triggering logic will not be maintained.
        """
        new_surveys = super().copy(default)
        if default and 'question_ids' in default:
            return new_surveys

        for old_survey, new_survey in zip(self, new_surveys):
            cloned_question_ids = new_survey.question_ids.sorted()

            answers_map = {
                src_answer.id: dst_answer.id
                for src, dst
                in zip(old_survey.question_ids, cloned_question_ids)
                for src_answer, dst_answer
                in zip(src.suggested_answer_ids, dst.suggested_answer_ids.sorted())
            }
            for src, dst in zip(old_survey.question_ids, cloned_question_ids):
                if src.triggering_answer_ids:
                    dst.triggering_answer_ids = [answers_map[src_answer_id.id] for src_answer_id in src.triggering_answer_ids]
        return new_surveys