def create(self, vals_list):
        """ Ensure we correctly assign sequences when creating steps.
        Indeed, sequences are very important within the script, and will break the whole flow if
        not correctly defined.

        This override will group created steps by chatbot_id and increment the sequence accordingly.
        It will also look for an existing step for that chatbot and resume from the highest sequence.

        This cannot be done in a default_value for the sequence field as we cannot search by
        runbot_id.
        It is also safer and more efficient to do it here (we can batch everything).

        It is still possible to manually pass the 'sequence' in the values, which will take priority. """

        vals_by_chatbot_id = {}
        for vals in vals_list:
            chatbot_id = vals.get('chatbot_script_id')
            if chatbot_id:
                step_values = vals_by_chatbot_id.get(chatbot_id, [])
                step_values.append(vals)
                vals_by_chatbot_id[chatbot_id] = step_values

        read_group_results = self.env['chatbot.script.step']._read_group(
            [('chatbot_script_id', 'in', list(vals_by_chatbot_id))],
            ['chatbot_script_id'],
            ['sequence:max'],
        )
        max_sequence_by_chatbot = {
            chatbot_script.id: sequence
            for chatbot_script, sequence in read_group_results
        }

        for chatbot_id, step_vals in vals_by_chatbot_id.items():
            current_sequence = 0
            if chatbot_id in max_sequence_by_chatbot:
                current_sequence = max_sequence_by_chatbot[chatbot_id] + 1

            for vals in step_vals:
                if 'sequence' in vals:
                    current_sequence = vals.get('sequence')
                else:
                    vals['sequence'] = current_sequence
                    current_sequence += 1

        return super().create(vals_list)