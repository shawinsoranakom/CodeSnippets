def _expire_individual_skills(self):
        """
        This function archive all individual skill in self.
        If the individual skill is not expired (valid_to < today) then valid_to will be set to yesterday if
        it's possible (not break a constraint)
        Else the individual skill is delete

        Example:
        An individual already have the skill English A2 (added one month ago) and we want to delete it
        output: [[1, id('English A2'), {'valid_to': yesterday}]]
        @return {List[COMMANDS]} List of WRITE, UNLINK commands
        """
        yesterday = fields.Date.today() - relativedelta(days=1)
        to_remove = self.env[self._name]
        to_archive = self.env[self._name]
        for individual_skill in self:
            if individual_skill.valid_from >= yesterday or (individual_skill.valid_to and individual_skill.valid_to <= yesterday):
                to_remove += individual_skill
            else:
                to_archive += individual_skill
        if to_archive:
            overlapping_dict = self._get_overlapping_individual_skill([{
                    f"{self._linked_field_name()}": skill[self._linked_field_name()].id,
                    "skill_id": skill.skill_id.id,
                    "id": skill.id,
                    "valid_from": skill.valid_from,
                    "valid_to": yesterday,
                    "skill_level_id": skill.skill_level_id.id,
                    "is_certification": skill.is_certification
            } for skill in to_archive])
            new_overlapped_skill_ids = []
            for new_skills in overlapping_dict.values():
                for new_skill in new_skills:
                    new_overlapped_skill_ids.append(new_skill['id'])
            changed_to_remove = to_archive.filtered(lambda ind_skill: ind_skill.id in new_overlapped_skill_ids)
            to_archive -= changed_to_remove
            to_remove += changed_to_remove
        return [[2, skill.id] for skill in to_remove] + [[1, skill.id, {'valid_to': yesterday}] for skill in to_archive]