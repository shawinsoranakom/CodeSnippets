def _create_individual_skills(self, vals_list):
        """
        This function transform CREATE commands into CREATE, WRITE and UNLINK commands in order to keep the
        logs and to follow the constraints

        Example:
        An individual already have the skill English A2 (added one month ago) and we want to add the skill English B1
        This method will transform:
        {linked_field: id, skill_id: id('English'), skill_level_id: id('B1') skill_type_id: id('Languages')}
        into
        [
            [1, id('English A2'), {'valid_to': yesterday}],
            [0, 0, {
                linked_field: id,
                skill_id: id('English'),
                skill_level_id: id('B1'),
                skill_type_id: id('Languages')}
            ]
        ]
        @param {List[vals]} vals_list: list of right leaf of CREATE commands
        @return {List[COMMANDS]} List of CREATE, WRITE, UNLINK commands
        """
        can_edit_certification_validity_period = self._can_edit_certification_validity_period()
        seen_skills = set()
        skills_to_archive = self.env[self._name]
        vals_to_return = []

        validity_domain = Domain.OR(
            [
                Domain("valid_to", "=", False),
                Domain("valid_to", ">=", fields.Date.today()),
            ]
        )

        if can_edit_certification_validity_period:
            validity_domain = Domain.OR([
                validity_domain,
                Domain("is_certification", "=", True),
            ])

        existing_skills_domain = Domain.AND(
            [
                Domain.OR(
                    [
                        Domain.AND(
                            [
                                Domain(f"{self._linked_field_name()}", "=", vals.get(self._linked_field_name(), False)),
                                Domain("skill_id", "=", vals.get("skill_id", False)),
                            ]
                        )
                        for vals in vals_list
                    ]
                ),
                validity_domain
            ]
        )

        existing_skills = self.env[self._name].search(existing_skills_domain)
        existing_skills_grouped = existing_skills.grouped(
            lambda skill: (skill[self._linked_field_name()].id, skill.skill_id.id)
        )

        if can_edit_certification_validity_period:
            existing_certifications = existing_skills.filtered(lambda s: s.is_certification)
            certification_set = {}
            for cert in existing_certifications:
                key = (
                    cert[self._linked_field_name()].id,
                    cert.skill_id.id,
                    cert.skill_level_id.id,
                    fields.Date.from_string(cert.valid_from),
                    fields.Date.from_string(cert.valid_to),
                )
                certification_set[key] = cert

            certification_types = set(
                self.env["hr.skill.type"]
                .browse([vals["skill_type_id"] for vals in vals_list])
                .filtered("is_certification")
                .ids
            )
        for vals in vals_list:
            individual_skill_id = vals.get(self._linked_field_name(), False)
            skill_id = vals["skill_id"]
            skill_type_id = vals["skill_type_id"]
            skill_level_id = vals["skill_level_id"]
            valid_from = fields.Date.from_string(vals.get("valid_from"))
            valid_to = fields.Date.from_string(vals.get("valid_to"))

            if can_edit_certification_validity_period:
                is_certificate = skill_type_id in certification_types
            else:
                is_certificate = False

            skill_key = (individual_skill_id, skill_id, valid_from, valid_to)

            # Remove duplicate skills
            if skill_key in seen_skills:
                continue
            seen_skills.add(skill_key)

            if is_certificate:
                key = (
                    individual_skill_id,
                    skill_id,
                    skill_level_id,
                    valid_from,
                    valid_to,
                )
                # Remove duplicate certification
                if certification_set.get(key):
                    continue
            else:
                # Archive existing regular skill if the person already have one with the same skill
                if existing_skill := existing_skills_grouped.get((individual_skill_id, skill_id)):
                    skills_to_archive += existing_skill

            vals_to_return.append(vals)

        return skills_to_archive._expire_individual_skills() + [[0, 0, new_create_val] for new_create_val in vals_to_return]