def _generate_template_recipients(self, res_ids, render_fields,
                                      allow_suggested=False,
                                      find_or_create_partners=False,
                                      render_results=None):
        """ Render recipients of the template 'self', returning values for records
        given by 'res_ids'. Default values can be generated instead of the template
        values if requested by template (see 'use_default_to' field). Email fields
        ('email_cc', 'email_to') are transformed into partners if requested
        (finding or creating partners). 'partner_to' field is transformed into
        'partner_ids' field.

        Note: for performance reason, information from records are transferred to
        created partners no matter the company. For example, if we have a record of
        company A and one of B with the same email and no related partner, a partner
        will be created with company A or B but populated with information from the 2
        records. So some info might be leaked from one company to the other through
        the partner.

        :param list res_ids: list of record IDs on which template is rendered;
        :param list render_fields: list of fields to render on template which
          are specific to recipients, e.g. email_cc, email_to, partner_to);
        :param boolean allow_suggested: when computing default recipients,
          include suggested recipients in addition to minimal defaults;
        :param boolean find_or_create_partners: transform emails into partners
          (calling ``find_or_create`` on partner model);
        :param dict render_results: res_ids-based dictionary of render values.
          For each res_id, a dict of values based on render_fields is given;

        :return: updated (or new) render_results. It holds a 'partner_ids' key
          holding partners given by ``_message_get_default_recipients`` and/or
          generated based on 'partner_to'. If ``find_or_create_partners`` is
          False emails are present, otherwise they are included as partners
          contained in ``partner_ids``.
        """
        self.ensure_one()
        if render_results is None:
            render_results = {}
        Model = self.env[self.model].with_prefetch(res_ids)

        # if using default recipients -> ``_message_get_default_recipients`` gives
        # values for email_to, email_cc and partner_ids; if using suggested recipients
        # -> ``_message_get_suggested_recipients_batch`` gives a list of potential
        # recipients (TODO: decide which API to keep)
        if self.use_default_to and self.model:
            if allow_suggested:
                suggested_recipients = Model.browse(res_ids)._message_get_suggested_recipients_batch(
                    reply_discussion=True, no_create=not find_or_create_partners,
                )
                for res_id, suggested_list in suggested_recipients.items():
                    pids = [r['partner_id'] for r in suggested_list if r['partner_id']]
                    email_to_lst = [
                        tools.mail.formataddr(
                            (r['name'] or '', r['email'] or '')
                        ) for r in suggested_list if not r['partner_id']
                    ]
                    render_results.setdefault(res_id, {})
                    render_results[res_id]['partner_ids'] = pids
                    render_results[res_id]['email_to'] = ', '.join(email_to_lst)
            else:
                default_recipients = Model.browse(res_ids)._message_get_default_recipients()
                for res_id, recipients in default_recipients.items():
                    render_results.setdefault(res_id, {}).update(recipients)
        # render fields dynamically which generates recipients
        else:
            for field in set(render_fields) & {'email_cc', 'email_to', 'partner_to'}:
                generated_field_values = self._render_field(field, res_ids)
                for res_id in res_ids:
                    render_results.setdefault(res_id, {})[field] = generated_field_values[res_id]

        # create partners from emails if asked to
        if find_or_create_partners:
            email_to_res_ids = {}
            records_emails = {}
            for record in Model.browse(res_ids):
                record_values = render_results.setdefault(record.id, {})
                mails = tools.email_split(record_values.pop('email_to', '')) + \
                        tools.email_split(record_values.pop('email_cc', ''))
                records_emails[record] = mails
                for mail in mails:
                    email_to_res_ids.setdefault(mail, []).append(record.id)

            if hasattr(Model, '_partner_find_from_emails'):
                records_partners = Model.browse(res_ids)._partner_find_from_emails(records_emails)
            else:
                records_partners = self.env['mail.thread']._partner_find_from_emails(records_emails)
            for res_id, partners in records_partners.items():
                render_results[res_id].setdefault('partner_ids', []).extend(partners.ids)

        # update 'partner_to' rendered value to 'partner_ids'
        all_partner_to = {
            pid
            for record_values in render_results.values()
            for pid in self._parse_partner_to(record_values.get('partner_to', ''))
        }
        existing_pids = set()
        if all_partner_to:
            existing_pids = set(self.env['res.partner'].sudo().browse(list(all_partner_to)).exists().ids)
        for record_values in render_results.values():
            partner_to = record_values.pop('partner_to', '')
            if partner_to:
                tpl_partner_ids = set(self._parse_partner_to(partner_to)) & existing_pids
                record_values.setdefault('partner_ids', []).extend(tpl_partner_ids)

        return render_results