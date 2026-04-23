def _map_applicant_skill_ids_to_talent_skill_ids(self, vals):
        """
        The applicant_skills_ids contains a list of ORM tuples i.e (command, record ID, {values})
        The challenge lies in the uniqueness of the record ID in this tuple. Each skill (e.g., 'arabic')
        has a distinct ID per applicant, i.e arabic in applicant 1 will have a different id from arabic in
        applicant 2. This means the content of applicant_skills_ids is unique for each record and attempting
        to pass it directly (e.g., applicant.pool_applicant_id.write(vals)) won't yield results so we must
        update each tuple to have the correct command and record ID for the talent pool applicant

        :param vals: list of CREATE, WRITE or UNLINK commands with skill_ids relevant to the applicant
        :return: list of CREATE, WRITE or UNLINK commands with skill_ids relevant to the pool_applicant
        """
        applicant_skills = {a.id: a.skill_id.id for a in self.applicant_skill_ids}
        applicant_skills_type = {a.id: a.skill_type_id.id for a in self.applicant_skill_ids}
        talent_skills = {a.skill_id.id: a.id for a in self.pool_applicant_id.applicant_skill_ids}
        mapped_commands = []
        for command in vals.get("applicant_skill_ids"):
            command_number = command[0]
            record_id = command[1]
            if command_number == Command.UPDATE:
                values = command[2]
                if applicant_skills[record_id] in talent_skills:
                    mapped_command = Command.update(talent_skills[applicant_skills[record_id]], values)
                    mapped_commands.append(mapped_command)
                else:
                    mapped_command = Command.create(
                        {
                            "skill_id": applicant_skills[record_id],
                            "skill_type_id": applicant_skills_type[record_id],
                            "skill_level_id": values["skill_level_id"],
                        },
                    )
                    mapped_commands.append(mapped_command)
            elif command_number == Command.DELETE:
                if applicant_skills[record_id] in talent_skills:
                    mapped_command = Command.delete(talent_skills[applicant_skills[record_id]])
                    mapped_commands.append(mapped_command)
            else:
                mapped_commands.append(command)
        return mapped_commands