def _generate_tracking_message(self, message, return_line='\n'):
        """
        Format the tracking values like in the chatter
        :param message: current mail.message record
        :param return_line: type of return line
        :return: a string with the new text if there is one or more tracking value
        """
        tracking_message = ''
        if message.subtype_id and message.subtype_id.description:
            tracking_message = return_line + message.subtype_id.description + return_line

        for tracking in message.sudo().tracking_value_ids._filter_free_field_access():
            if tracking.field_id.ttype == 'boolean':
                old_value = str(bool(tracking.old_value_integer))
                new_value = str(bool(tracking.new_value_integer))
            else:
                old_value = tracking.old_value_char or str(tracking.old_value_integer)
                new_value = tracking.new_value_char or str(tracking.new_value_integer)

            tracking_message += tracking.field_id.field_description + ': ' + old_value
            if old_value != new_value:
                tracking_message += ' → ' + new_value
            tracking_message += return_line

        return tracking_message