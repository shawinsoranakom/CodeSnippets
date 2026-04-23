def _compute_plan_schedule_line_ids(self):
        self.plan_schedule_line_ids = False
        for scheduler in self:
            schedule_line_values_list = []
            for template in scheduler.plan_id.template_ids:
                schedule_line_values = {
                    'line_description': template.summary or template.activity_type_id.name,
                }

                # try to determine responsible user, light re-coding of '_determine_responsible' but
                # we don't always have a target record here
                responsible_user = False
                res_ids = scheduler._evaluate_res_ids()
                if template.responsible_id:
                    responsible_user = template.responsible_id
                elif template.responsible_type == 'on_demand':
                    responsible_user = scheduler.plan_on_demand_user_id
                elif scheduler.res_model and res_ids and len(res_ids) == 1:
                    record = self.env[scheduler.res_model].browse(res_ids)
                    if record.exists():
                        responsible_user = template._determine_responsible(
                            scheduler.plan_on_demand_user_id,
                            record,
                        )['responsible']

                if responsible_user:
                    schedule_line_values['responsible_user_id'] = responsible_user.id

                activity_date_deadline = False
                if scheduler.plan_date:
                    activity_date_deadline = template._get_date_deadline(scheduler.plan_date)
                    schedule_line_values['line_date_deadline'] = activity_date_deadline

                # append main line before handling next activities
                schedule_line_values_list.append(schedule_line_values)

                activity_type = template.activity_type_id
                if activity_type.triggered_next_type_id:
                    next_activity = activity_type.triggered_next_type_id
                    schedule_line_values = {
                        'line_description': next_activity.summary or next_activity.name,
                        'responsible_user_id': next_activity.default_user_id.id or False
                    }
                    if activity_date_deadline:
                        schedule_line_values['line_date_deadline'] = next_activity.with_context(
                            activity_previous_deadline=activity_date_deadline
                        )._get_date_deadline()

                    schedule_line_values_list.append(schedule_line_values)
                elif activity_type.suggested_next_type_ids:
                    for suggested in activity_type.suggested_next_type_ids:
                        schedule_line_values = {
                            'line_description': suggested.summary or suggested.name,
                            'responsible_user_id': suggested.default_user_id.id or False,
                        }
                        if activity_date_deadline:
                            schedule_line_values['line_date_deadline'] = suggested.with_context(
                                activity_previous_deadline=activity_date_deadline
                            )._get_date_deadline()

                        schedule_line_values_list.append(schedule_line_values)

                scheduler.plan_schedule_line_ids = [(5,)] + [(0, 0, values) for values in schedule_line_values_list]