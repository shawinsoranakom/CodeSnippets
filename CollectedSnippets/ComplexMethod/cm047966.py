def _post_completion_update_hook(self, completed=True):
        res = super()._post_completion_update_hook(completed)
        if not completed:
            return res
        completed_membership = self.filtered(lambda m: m.member_status == 'completed')
        if not completed_membership:
            return res
        partner_has_completed = {
            membership.partner_id.id: membership.channel_id
            for membership in completed_membership
        }
        employees = self.env['hr.employee'].sudo().search(
            [('user_id.partner_id', 'in', completed_membership.partner_id.ids)])

        if employees:
            HrResumeLine = self.env['hr.resume.line'].sudo()
            line_type = self.env.ref('hr_skills.resume_type_training', raise_if_not_found=False)
            line_type_id = line_type and line_type.id

            lines_for_channel_by_employee = dict(HrResumeLine._read_group([
                ('employee_id', 'in', employees.ids),
                ('channel_id', 'in', completed_membership.channel_id.ids),
                ('line_type_id', '=', line_type_id)
            ], ['employee_id'], ['channel_id:array_agg']))

            lines_to_create = []
            for employee in employees:
                channel = partner_has_completed[employee.user_id.partner_id.id]

                if channel.id not in lines_for_channel_by_employee.get(employee, []):
                    lines_to_create.append({
                        'employee_id': employee.id,
                        'name': channel.name,
                        'date_start': fields.Date.today(),
                        'description': html2plaintext(channel.description),
                        'line_type_id': line_type_id,
                        'course_type': 'elearning',
                        'channel_id': channel.id,
                    })
            if lines_to_create:
                HrResumeLine.create(lines_to_create)
        return res