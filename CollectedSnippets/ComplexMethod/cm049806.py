def _check_bounce_catchall_uniqueness(self):
        names = self.filtered('bounce_alias').mapped('bounce_alias') + self.filtered('catchall_alias').mapped('catchall_alias')
        if not names:
            return

        similar_domains = self.env['mail.alias.domain'].search([('name', 'in', self.mapped('name'))])
        for tocheck in self:
            if any(similar.bounce_alias == tocheck.bounce_alias
                   for similar in similar_domains if similar != tocheck and similar.name == tocheck.name):
                raise exceptions.ValidationError(
                    _('Bounce alias %(bounce)s is already used for another domain with same name. '
                      'Use another bounce or simply use the other alias domain.',
                      bounce=tocheck.bounce_email)
                )
            if any(similar.catchall_alias == tocheck.catchall_alias
                   for similar in similar_domains if similar != tocheck and similar.name == tocheck.name):
                raise exceptions.ValidationError(
                    _('Catchall alias %(catchall)s is already used for another domain with same name. '
                      'Use another catchall or simply use the other alias domain.',
                      catchall=tocheck.catchall_email)
                )

        # search on left-part only to speedup, then filter on right part
        potential_aliases = self.env['mail.alias'].search([
            ('alias_name', 'in', list(set(names))),
            ('alias_domain_id', '!=', False)
        ])
        existing = next(
            (alias for alias in potential_aliases
             if alias.display_name in (self.mapped('bounce_email') + self.mapped('catchall_email'))),
            self.env['mail.alias']
        )
        if existing:
            document_name = False
            # If owner or target: display document name also in the warning
            if existing.alias_parent_model_id and existing.alias_parent_thread_id:
                document_name = self.env[existing.alias_parent_model_id.model].sudo().browse(existing.alias_parent_thread_id).display_name
            elif existing.alias_model_id and existing.alias_force_thread_id:
                document_name = self.env[existing.alias_model_id.model].sudo().browse(existing.alias_force_thread_id).display_name
            if document_name:
                raise exceptions.ValidationError(
                    _("Bounce/Catchall '%(matching_alias_name)s' is already used by %(document_name)s. Choose another alias or change it on the other document.",
                      matching_alias_name=existing.display_name,
                      document_name=document_name)
                        )
            raise exceptions.ValidationError(
                _("Bounce/Catchall '%(matching_alias_name)s' is already used. Choose another alias or change it on the linked model.",
                  matching_alias_name=existing.display_name)
            )