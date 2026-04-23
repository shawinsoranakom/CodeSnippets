def _check_unique(self, alias_names, alias_domains):
        """ Check unicity constraint won't be raised, otherwise raise a UserError
        with a complete error message. Also check unicity against alias config
        parameters.

        :param list alias_names: a list of names (considered as sanitized
          and ready to be sent to DB);
        :param list alias_domains: list of alias_domain records under which
          the check is performed, as uniqueness is performed for given pair
          (name, alias_domain);
        """
        if len(alias_names) != len(alias_domains):
            msg = (f"Invalid call to '_check_unique': names and domains should make coherent lists, "
                   f"received {', '.join(alias_names)} and {', '.join(alias_domains.mapped('name'))}")
            raise ValueError(msg)

        # reorder per alias domain, keep only not void alias names (void domain also checks uniqueness)
        domain_to_names = defaultdict(list)
        for alias_name, alias_domain in zip(alias_names, alias_domains):
            if alias_name and alias_name in domain_to_names[alias_domain]:
                raise UserError(
                    _('Email aliases %(alias_name)s cannot be used on several records at the same time. Please update records one by one.',
                      alias_name=alias_name)
                )
            if alias_name:
                domain_to_names[alias_domain].append(alias_name)

        # matches existing alias
        domain = Domain.OR(
            Domain('alias_name', 'in', alias_names) & Domain('alias_domain_id', '=', alias_domain.id)
            for alias_domain, alias_names in domain_to_names.items()
        )
        if domain and self:
            domain &= Domain('id', 'not in', self.ids)
        existing = self.search(domain, limit=1) if domain else self.env['mail.alias']
        if not existing:
            return
        if existing.alias_parent_model_id and existing.alias_parent_thread_id:
            parent_name = self.env[existing.alias_parent_model_id.model].sudo().browse(existing.alias_parent_thread_id).display_name
            msg_begin = _(
                'Alias %(matching_name)s (%(current_id)s) is already linked with %(alias_model_name)s (%(matching_id)s) and used by the %(parent_name)s %(parent_model_name)s.',
                alias_model_name=existing.alias_model_id.name,
                current_id=self.ids if self else _('your alias'),
                matching_id=existing.id,
                matching_name=existing.display_name,
                parent_name=parent_name,
                parent_model_name=existing.alias_parent_model_id.name
            )
        else:
            msg_begin = _(
                'Alias %(matching_name)s (%(current_id)s) is already linked with %(alias_model_name)s (%(matching_id)s).',
                alias_model_name=existing.alias_model_id.name,
                current_id=self.ids if self else _('new'),
                matching_id=existing.id,
                matching_name=existing.display_name,
            )
        msg_end = _('Choose another value or change it on the other document.')
        raise UserError(f'{msg_begin} {msg_end}')