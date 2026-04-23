def _check_alias_domain_id_mc(self):
        """ Check for invalid alias domains based on company configuration.
        When having a parent record and/or updating an existing record alias
        domain should match the one used on the related record. """

        # in sudo, to be able to read alias_parent_model_id (ir.model)
        tocheck = self.sudo().filtered(lambda alias: alias.alias_domain_id.company_ids)
        # transient check, mainly for tests / install
        tocheck = tocheck.filtered(lambda alias:
            (not alias.alias_model_id.model or alias.alias_model_id.model in self.env) and
            (not alias.alias_parent_model_id.model or alias.alias_parent_model_id.model in self.env)
        )
        if not tocheck:
            return

        # helpers to find owner / target models
        def _owner_model(alias):
            return alias.alias_parent_model_id.model
        def _owner_env(alias):
            return self.env[_owner_model(alias)]
        def _target_model(alias):
            return alias.alias_model_id.model
        def _target_env(alias):
            return self.env[_target_model(alias)]

        # fetch impacted records, classify by model
        recs_by_model = defaultdict(list)
        for alias in tocheck:
            # owner record (like 'project.project' for aliases creating new 'project.task')
            if alias.alias_parent_model_id and alias.alias_parent_thread_id:
                if _owner_env(alias)._mail_get_company_field():
                    recs_by_model[_owner_model(alias)].append(alias.alias_parent_thread_id)
            # target record (like 'mail.group' updating a given group)
            if alias.alias_model_id and alias.alias_force_thread_id:
                if _target_env(alias)._mail_get_company_field():
                    recs_by_model[_target_model(alias)].append(alias.alias_force_thread_id)

        # helpers to fetch owner / target with prefetching
        def _fetch_owner(alias):
            if alias.alias_parent_thread_id in recs_by_model[alias.alias_parent_model_id.model]:
                return _owner_env(alias).with_prefetch(
                    recs_by_model[_owner_model(alias)]
                ).browse(alias.alias_parent_thread_id)
            return None
        def _fetch_target(alias):
            if alias.alias_force_thread_id in recs_by_model[alias.alias_model_id.model]:
                return _target_env(alias).with_prefetch(
                    recs_by_model[_target_model(alias)]
                ).browse(alias.alias_force_thread_id)
            return None

        # check company domains are compatible
        for alias in tocheck:
            if owner := _fetch_owner(alias):
                company = owner[owner._mail_get_company_field()]
                if company and company.alias_domain_id != alias.alias_domain_id and alias.alias_domain_id.company_ids:
                    raise ValidationError(_(
                        "We could not create alias %(alias_name)s because domain "
                        "%(alias_domain_name)s belongs to company %(alias_company_names)s "
                        "while the owner document belongs to company %(company_name)s.",
                        alias_company_names=','.join(alias.alias_domain_id.company_ids.mapped('name')),
                        alias_domain_name=alias.alias_domain_id.name,
                        alias_name=alias.display_name,
                        company_name=company.name,
                    ))
            if target := _fetch_target(alias):
                company = target[target._mail_get_company_field()]
                if company and company.alias_domain_id != alias.alias_domain_id and alias.alias_domain_id.company_ids:
                    raise ValidationError(_(
                        "We could not create alias %(alias_name)s because domain "
                        "%(alias_domain_name)s belongs to company %(alias_company_names)s "
                        "while the target document belongs to company %(company_name)s.",
                        alias_company_names=','.join(alias.alias_domain_id.company_ids.mapped('name')),
                        alias_domain_name=alias.alias_domain_id.name,
                        alias_name=alias.display_name,
                        company_name=company.name,
                    ))