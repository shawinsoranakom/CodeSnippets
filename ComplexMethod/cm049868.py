def get_empty_list_help(self, help_message):
        """ Override of BaseModel.get_empty_list_help() to generate an help message
        that adds alias information. """
        model = self.env.context.get('empty_list_help_model')
        res_id = self.env.context.get('empty_list_help_id')
        document_name = self.env.context.get('empty_list_help_document_name', _('document'))
        nothing_here = is_html_empty(help_message)
        alias = None

        # specific res_id -> find its alias (i.e. section_id specified)
        if model and res_id:
            record = self.env[model].sudo().browse(res_id)
            # check that the alias effectively creates new records
            if ('alias_id' in record and record.alias_id and
                record.alias_id.alias_name and record.alias_id.alias_domain and
                record.alias_id.alias_model_id.model == self._name and
                record.alias_id.alias_force_thread_id == 0):
                alias = record.alias_id
        # no res_id or res_id not linked to an alias -> generic help message, take a generic alias of the model
        if not alias and model and self.env.company.alias_domain_id:
            aliases = self.env['mail.alias'].search([
                ("alias_domain_id", "=", self.env.company.alias_domain_id.id),
                ("alias_parent_model_id.model", "=", model),
                ("alias_name", "!=", False),
                ('alias_force_thread_id', '=', False),
                ('alias_parent_thread_id', '=', False)], order='id ASC')
            if aliases and len(aliases) == 1:
                alias = aliases[0]

        if alias:
            email_link = Markup("<a href='mailto:%s'>%s</a>") % (alias.display_name, alias.display_name)
            if nothing_here:
                dyn_help = _("Add a new %(document)s or send an email to %(email_link)s",
                             document=html_escape(document_name),
                             email_link=email_link,
                            )
                return super().get_empty_list_help(f"<p class='o_view_nocontent_smiling_face'>{dyn_help}</p>")
            # do not add alias two times if it was added previously
            if "oe_view_nocontent_alias" not in help_message:
                dyn_help = _("Create new %(document)s by sending an email to %(email_link)s",
                             document=html_escape(document_name),
                             email_link=email_link,
                            )
                return super().get_empty_list_help(f"{help_message}<p class='oe_view_nocontent_alias'>{dyn_help}</p>")

        if nothing_here:
            dyn_help = _("Create new %(document)s", document=html_escape(document_name))
            return super().get_empty_list_help(f"<p class='o_view_nocontent_smiling_face'>{dyn_help}</p>")

        return super().get_empty_list_help(help_message)