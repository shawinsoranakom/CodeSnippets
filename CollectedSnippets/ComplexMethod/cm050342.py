def _get_transformed_commands(self, commands, individuals):
        """
        Transform a list of ORM commands to fit with the business constraints and preserve the logic of how skills and
        certifications should behave. The key behaviors are as follows:

        Skills:
        1. Only one active skill per `skill_id` is allowed (e.g., one "English" skill per linked_field record).

        Certifications (`is_certification=True`):
        1. Multiple certifications with the same `skill_id` and `level_id` are allowed if their date ranges differ (e.g.,
            "Odoo Certified (2024-01-01 → 2024-12-31)" and "Odoo Certified (2024-06-01 → 2025-05-31)" can coexist.)

        Shared Rules:
        - Updates always create new records (archiving old ones) rather than in-place writes.
        - No two records can have all their fields identical.
        - A skill/certification is active if `valid_to` is unset or in the future.
        - A skill/certification that is not active is considered archived.
        - A skill/certification is only deleted if valid_from is from the past 24 hours or it is expired.

        :param commands: list of CREATE, WRITE, and UNLINK commands
        :param individuals: a recordset of linked_field's model
        :return: List of CREATE, WRITE, and UNLINK commands
        """
        if not commands:
            return
        updated_ids = set()
        updated_commands = []
        created_values = []
        unlinked_ids = set()
        for command in commands:
            if command[0] == 1:
                updated_ids.add(command[1])
                updated_commands.append(command)
            elif command[0] == 2:
                unlinked_ids.add(command[1])
            elif command[0] == 0:
                if individuals:
                    for individual in individuals:
                        individual_command = command[2]
                        individual_command[self._linked_field_name()] = individual.id
                        created_values.append(individual_command)
                else:
                    created_values.append(command[2])
        mixed_command_ids = list(updated_ids & unlinked_ids)
        if mixed_command_ids:
            # reset updated values
            updated_ids = set()
            updated_commands = []
            for command in commands:
                if command[1] not in mixed_command_ids and command[0] == 1:
                    updated_commands.append(command)
                    updated_ids.append(command[1])
        # Process individual_skill_ids values
        unlinked_commands = self.env[self._name].browse(list(unlinked_ids))._expire_individual_skills()
        updated_commands = self.env[self._name].browse(list(updated_ids))._write_individual_skills(updated_commands)
        created_commands = self.env[self._name]._create_individual_skills(created_values)
        return unlinked_commands + updated_commands + created_commands