def _generate_template(self, res_ids, render_fields,
                           recipients_allow_suggested=False,
                           find_or_create_partners=False):
        """ Render values from template 'self' on records given by 'res_ids'.
        Those values are generally used to create a mail.mail or a mail.message.
        Model of records is the one defined on template.

        :param list res_ids: list of record IDs on which template is rendered;
        :param list render_fields: list of fields to render on template;

        # recipients generation
        :param boolean recipients_allow_suggested: when computing default
          recipients, include suggested recipients in addition to minimal
          defaults;
        :param boolean find_or_create_partners: transform emails into partners
          (see ``_generate_template_recipients``);

        :returns: a dict of (res_ids, values) where values contains all rendered
          fields asked in ``render_fields``. Asking for attachments adds an
          'attachments' key using the format [(report_name, data)] where data
          is base64 encoded. Asking for recipients adds a 'partner_ids' key.
          Note that 2many fields contain a list of IDs, not commands.
        """
        self.ensure_one()
        render_fields_set = set(render_fields)
        fields_specific = {
            'attachment_ids',  # attachments
            'email_cc',  # recipients
            'email_to',  # recipients
            'partner_to',  # recipients
            'report_template_ids',  # attachments
            'scheduled_date',  # specific
            # not rendered (static)
            'auto_delete',
            'email_layout_xmlid',
            'mail_server_id',
            'model',
            'res_id',
        }

        render_results = {}
        for (template, template_res_ids) in self._classify_per_lang(res_ids).values():
            # render fields not rendered by sub methods
            fields_torender = {
                field for field in render_fields_set
                if field not in fields_specific
            }
            for field in fields_torender:
                generated_field_values = template._render_field(
                    field, template_res_ids
                )
                for res_id, field_value in generated_field_values.items():
                    render_results.setdefault(res_id, {})[field] = field_value

            # render recipients
            if render_fields_set & {'email_cc', 'email_to', 'partner_to'}:
                template._generate_template_recipients(
                    template_res_ids, render_fields_set,
                    render_results=render_results,
                    allow_suggested=recipients_allow_suggested,
                    find_or_create_partners=find_or_create_partners
                )

            # render scheduled_date
            if 'scheduled_date' in render_fields_set:
                template._generate_template_scheduled_date(
                    template_res_ids,
                    render_results=render_results
            )

            # add values static for all res_ids
            template._generate_template_static_values(
                template_res_ids,
                render_fields_set,
                render_results=render_results
            )

            # generate attachments if requested
            if render_fields_set & {'attachment_ids', 'report_template_ids'}:
                template._generate_template_attachments(
                    template_res_ids,
                    render_fields_set,
                    render_results=render_results
                )

        return render_results