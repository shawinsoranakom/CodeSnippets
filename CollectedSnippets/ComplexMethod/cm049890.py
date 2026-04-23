def _message_create(self, values_list):
        """ Low-level helper to create mail.message records. It is mainly used
        to hide the cleanup of given values, for mail gateway or helpers."""
        values_list = [
            {
                key: val
                for key, val in values.items()
                if key not in self._get_message_create_ignore_field_names()
            }
            for values in values_list
        ]
        create_values_list = []

        # preliminary value safety check
        self._raise_for_invalid_parameters(
            {key for values in values_list for key in values.keys()},
            restricting_names=self._get_message_create_valid_field_names()
        )

        for values in values_list:
            create_values = dict(values)
            create_values['partner_ids'] = [(4, pid) for pid in (create_values.get('partner_ids') or [])]
            create_values_list.append(create_values)

        # remove context, notably for default keys, as this thread method is not
        # meant to propagate default values for messages, only for master records
        return self.env['mail.message'].with_context(
            clean_context(self.env.context)
        ).create(create_values_list)