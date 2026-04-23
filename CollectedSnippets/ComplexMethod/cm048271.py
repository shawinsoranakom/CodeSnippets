def copy(self, default=None):
        """ Correctly copy the 'triggering_answer_ids' field from the original script_step_ids to the clone.
        This needs to be done in post-processing to make sure we get references to the newly created
        answers from the copy instead of references to the answers of the original.

        This implementation assumes that the order of created steps and answers will be kept between
        the original and the clone, using 'zip()' to match the records between the two. """
        default = default or {}
        new_scripts = super().copy(default=default)
        if 'question_ids' in default:
            return new_scripts

        for old_script, new_script in zip(self, new_scripts):
            original_steps = old_script.script_step_ids.sorted()
            clone_steps = new_script.script_step_ids.sorted()

            answers_map = {}
            for clone_step, original_step in zip(clone_steps, original_steps):
                for clone_answer, original_answer in zip(clone_step.answer_ids.sorted(), original_step.answer_ids.sorted()):
                    answers_map[original_answer] = clone_answer

            for clone_step, original_step in zip(clone_steps, original_steps):
                clone_step.write({
                    'triggering_answer_ids': [
                        (4, answer.id)
                        for answer in [
                            answers_map[original_answer]
                            for original_answer
                            in original_step.triggering_answer_ids
                        ]
                    ]
                })
        return new_scripts