def _compute_kpis(self, company, user):
        """ Compute KPIs to display in the digest template. It is expected to be
        a list of KPIs, each containing values for 3 columns display.

        :return: result [{
            'kpi_name': 'kpi_mail_message',
            'kpi_fullname': 'Messages',  # translated
            'kpi_action': 'crm.crm_lead_action_pipeline',  # xml id of an action to execute
            'kpi_col1': {
                'value': '12.0',
                'margin': 32.36,
                'col_subtitle': 'Yesterday',  # translated
            },
            'kpi_col2': { ... },
            'kpi_col3':  { ... },
        }, { ... }] """
        self.ensure_one()
        digest_fields = self._get_kpi_fields()
        invalid_fields = []
        kpis = [
            dict(kpi_name=field_name,
                 kpi_fullname=self.env['ir.model.fields']._get(self._name, field_name).field_description,
                 kpi_action=False,
                 kpi_col1=dict(),
                 kpi_col2=dict(),
                 kpi_col3=dict(),
                 )
            for field_name in digest_fields
        ]
        kpis_actions = self._compute_kpis_actions(company, user)

        for col_index, (tf_name, tf) in enumerate(self._compute_timeframes(company)):
            digest = self.with_context(start_datetime=tf[0][0], end_datetime=tf[0][1]).with_user(user).with_company(company)
            previous_digest = self.with_context(start_datetime=tf[1][0], end_datetime=tf[1][1]).with_user(user).with_company(company)
            for index, field_name in enumerate(digest_fields):
                kpi_values = kpis[index]
                kpi_values['kpi_action'] = kpis_actions.get(field_name)
                try:
                    compute_value = digest[field_name + '_value']
                    # Context start and end date is different each time so invalidate to recompute.
                    digest.invalidate_model([field_name + '_value'])
                    previous_value = previous_digest[field_name + '_value']
                    # Context start and end date is different each time so invalidate to recompute.
                    previous_digest.invalidate_model([field_name + '_value'])
                except AccessError:  # no access rights -> just skip that digest details from that user's digest email
                    invalid_fields.append(field_name)
                    continue
                margin = self._get_margin_value(compute_value, previous_value)
                if self._fields['%s_value' % field_name].type == 'monetary':
                    converted_amount = tools.misc.format_decimalized_amount(compute_value)
                    compute_value = self._format_currency_amount(converted_amount, company.currency_id)
                elif self._fields['%s_value' % field_name].type == 'float':
                    compute_value = "%.2f" % compute_value

                kpi_values['kpi_col%s' % (col_index + 1)].update({
                    'value': compute_value,
                    'margin': margin,
                    'col_subtitle': tf_name,
                })

        # filter failed KPIs
        return [kpi for kpi in kpis if kpi['kpi_name'] not in invalid_fields]