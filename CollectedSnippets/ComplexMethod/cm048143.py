def _attendees_values(self, partner_commands):
        """
        :param partner_commands: ORM commands for partner_id field (0 and 1 commands not supported)
        :return: associated attendee_ids ORM commands
        """
        attendee_commands = []

        removed_partner_ids = []
        added_partner_ids = []

        # if commands are just integers, assume they are ids with the intent to `Command.set`
        if partner_commands and isinstance(partner_commands[0], int):
            partner_commands = [Command.set(partner_commands)]

        for command in partner_commands:
            op = command[0]
            if op in (2, 3, Command.delete, Command.unlink):  # Remove partner
                removed_partner_ids += [command[1]]
            elif op in (6, Command.set):  # Replace all
                removed_partner_ids += set(self.partner_ids.ids) - set(command[2])  # Don't recreate attendee if partner already attend the event
                added_partner_ids += set(command[2]) - set(self.partner_ids.ids)
            elif op in (4, Command.link):
                added_partner_ids += [command[1]] if command[1] not in self.partner_ids.ids else []
            # commands 0 and 1 not supported

        if not self:
            attendees_to_unlink = self.env['calendar.attendee']
        else:
            attendees_to_unlink = self.env['calendar.attendee'].search([
                ('event_id', 'in', self.ids),
                ('partner_id', 'in', removed_partner_ids),
            ])
        attendee_commands += [[2, attendee.id] for attendee in attendees_to_unlink]  # Removes and delete

        attendee_commands += [
            [0, 0, dict(partner_id=partner_id)]
            for partner_id in added_partner_ids
        ]
        return attendee_commands