def action_schedule_plan(self):
        if not self.res_model:
            raise ValueError(_('Plan-based scheduling are available only on documents.'))
        applied_on = self._get_applied_on_records()
        for record in applied_on:
            body = _('The plan "%(plan_name)s" has been started', plan_name=self.plan_id.name)
            activity_descriptions = []
            for template in self._plan_filter_activity_templates_to_schedule():
                if template.responsible_type == 'on_demand':
                    responsible = self.plan_on_demand_user_id
                else:
                    responsible = template._determine_responsible(self.plan_on_demand_user_id, record)['responsible']
                date_deadline = template._get_date_deadline(self.plan_date)
                record.activity_schedule(
                    activity_type_id=template.activity_type_id.id,
                    automated=False,
                    summary=template.summary,
                    note=template.note,
                    user_id=responsible.id,
                    date_deadline=date_deadline
                )
                activity_descriptions.append(
                    _('%(activity)s, assigned to %(name)s, due on the %(deadline)s',
                      activity=template.summary or template.activity_type_id.name,
                      name=responsible.name, deadline=format_date(self.env, date_deadline)))

            if activity_descriptions:
                body += Markup('<ul>%s</ul>') % (
                    Markup().join(Markup('<li>%s</li>') % description for description in activity_descriptions)
                )
            record.message_post(body=body)

        if len(applied_on) == 1:
            return {'type': 'ir.actions.client', 'tag': 'soft_reload'}

        return {
            'type': 'ir.actions.act_window',
            'res_model': self.res_model,
            'name': _('Launch Plans'),
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('id', 'in', applied_on.ids)],
        }