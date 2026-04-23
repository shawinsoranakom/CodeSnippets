def _get_overlapping_individual_skill(self, vals_list):
        can_edit_certification_validity_period = self._can_edit_certification_validity_period()
        matching_skill_domain = Domain.FALSE
        overlapping_dict = defaultdict(list)
        certification_dict = defaultdict(list)
        regular_dict = defaultdict(list)
        for individual_skill_vals in vals_list:
            ind_domain = Domain.AND([
                Domain(f"{self._linked_field_name()}.id", "=", individual_skill_vals[self._linked_field_name()]),
                Domain("skill_id.id", "=", individual_skill_vals['skill_id']),
                Domain("id", "!=", individual_skill_vals['id']),
            ])

            if can_edit_certification_validity_period and individual_skill_vals['is_certification']:
                ind_domain = Domain.AND([
                    ind_domain,
                    Domain("skill_level_id.id", "=", individual_skill_vals['skill_level_id']),
                    Domain('valid_from', '=', individual_skill_vals['valid_from']),
                    Domain('valid_to', '=', individual_skill_vals['valid_to']),
                ])
                key = (
                    individual_skill_vals[self._linked_field_name()],
                    individual_skill_vals['skill_id'],
                    individual_skill_vals['skill_level_id'],
                    fields.Date.from_string(individual_skill_vals['valid_from']),
                    fields.Date.from_string(individual_skill_vals['valid_to']),
                )
                certification_dict[key].append(individual_skill_vals)
            else:
                ind_domain = Domain.AND([
                    ind_domain,
                    Domain.OR([
                        Domain.AND([
                            Domain('valid_from', '<=', individual_skill_vals['valid_from']),
                            Domain.OR([
                                Domain('valid_to', '=', False),
                                Domain('valid_to', '>=', individual_skill_vals['valid_from']),
                            ]),
                        ]),
                        Domain.AND([
                            Domain('valid_from', '<=', individual_skill_vals['valid_to']),
                            Domain.OR([
                                Domain('valid_to', '=', False),
                                Domain('valid_to', '>=', individual_skill_vals['valid_to']),
                            ]),
                        ]),
                    ])
                ])

                key = (
                    individual_skill_vals[self._linked_field_name()],
                    individual_skill_vals['skill_id'],
                )
                regular_dict[key].append(individual_skill_vals)

            matching_skill_domain = Domain.OR([matching_skill_domain, ind_domain])
        matching_individual_skills = self.env[self._name].search(matching_skill_domain)
        for matching_ind_skill in matching_individual_skills:
            if can_edit_certification_validity_period and matching_ind_skill.is_certification:
                similar_certifications = certification_dict.get((
                    matching_ind_skill[self._linked_field_name()].id,
                    matching_ind_skill.skill_id.id,
                    matching_ind_skill.skill_level_id.id,
                    fields.Date.from_string(matching_ind_skill.valid_from),
                    fields.Date.from_string(matching_ind_skill.valid_to),
                ))
                if similar_certifications:
                    overlapping_dict[matching_ind_skill].extend(similar_certifications)
            else:
                similar_regular_skills = regular_dict.get((
                    matching_ind_skill[self._linked_field_name()].id,
                    matching_ind_skill.skill_id.id,
                ), [])
                for similar_regular_skill in similar_regular_skills:
                    if (matching_ind_skill.valid_from <= similar_regular_skill['valid_from'] and
                        (not matching_ind_skill.valid_to or
                        matching_ind_skill.valid_to >= similar_regular_skill['valid_from']
                    )) or (matching_ind_skill.valid_from <= similar_regular_skill['valid_to'] and
                        (not matching_ind_skill.valid_to or
                        matching_ind_skill.valid_to >= similar_regular_skill['valid_to']
                    )):
                        overlapping_dict[matching_ind_skill].append(similar_regular_skill)
        return overlapping_dict