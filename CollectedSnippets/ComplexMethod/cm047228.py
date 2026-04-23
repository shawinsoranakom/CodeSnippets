def _get_warning_messages(self):
        self.ensure_one()
        warnings = []

        if self.model_id and (children_with_different_model := self.child_ids.filtered(lambda a: a.model_id != self.model_id)):
            warnings.append(_("Following child actions should have the same model (%(model)s): %(children)s",
                              model=self.model_id.name,
                              children=', '.join(children_with_different_model.mapped('name'))))

        if self.group_ids and (children_with_different_groups := self.child_ids.filtered(lambda a: a.group_ids != self.group_ids)):
            warnings.append(_("Following child actions should have the same groups (%(groups)s): %(children)s",
                              groups=', '.join(self.group_ids.mapped('name')),
                              children=', '.join(children_with_different_groups.mapped('name'))))

        if (children_with_warnings := self.child_ids.filtered('warning')):
            warnings.append(_("Following child actions have warnings: %(children)s", children=', '.join(children_with_warnings.mapped('name'))))

        if (relation_chain := self._get_relation_chain("update_path")) and relation_chain[0] and isinstance(relation_chain[0][-1], fields.Json):
            warnings.append(_("I'm sorry to say that JSON fields (such as '%s') are currently not supported.", relation_chain[0][-1].string))

        if self.state == 'object_write' and self.evaluation_type == 'sequence' and self.update_field_type and self.update_field_type not in ('char', 'text'):
            warnings.append(_("A sequence must only be used with character fields."))

        if self.state == 'webhook' and self.model_id:
            restricted_fields = []
            Model = self.env[self.model_id.model]
            for model_field in self.webhook_field_ids:
                # you might think that the ir.model.field record holds references
                # to the groups, but that's not the case - we need to field object itself
                field = Model._fields[model_field.name]
                if field.groups:
                    restricted_fields.append(f"- {model_field.field_description}")
            if restricted_fields:
                warnings.append(_("Group-restricted fields cannot be included in "
                                "webhook payloads, as it could allow any user to "
                                "accidentally leak sensitive information. You will "
                                "have to remove the following fields from the webhook payload:\n%(restricted_fields)s", restricted_fields="\n".join(restricted_fields)))

        return warnings