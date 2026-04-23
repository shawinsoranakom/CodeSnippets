def get_internal_resume_lines(self, res_id, res_model):
        if not res_id:
            return []
        if res_model == 'res.users':
            res_id = self.env['res.users'].browse(res_id).employee_id.id
        if not self.env['hr.employee.public'].browse(res_id).has_access('read'):
            raise AccessError(self.env._("You cannot access the resume of this employee."))
        res = []
        employee_versions = self.env['hr.employee'].sudo().browse(res_id).version_ids
        if not employee_versions:
            return res
        interval_date_start = False
        for i in range(len(employee_versions) - 1):
            current_version = employee_versions[i]
            next_version = employee_versions[i + 1]
            current_date_start = max(current_version.date_version, current_version.contract_date_start or date.min)
            current_date_end = min(next_version.date_version + relativedelta(days=-1), current_version.contract_date_end or date.max)
            if not current_version.job_title:
                if interval_date_start:
                    previous_version = employee_versions[i - 1]
                    res.append({
                        'id': previous_version.id,
                        'job_title': previous_version.job_title,
                        'date_start': interval_date_start,
                        'date_end': current_date_start + relativedelta(days=-1),
                    })
                    interval_date_start = False
            elif current_version.job_title != next_version.job_title or current_date_end + relativedelta(days=1) != next_version.date_version:
                res.append({
                    'id': current_version.id,
                    'job_title': current_version.job_title,
                    'date_start': interval_date_start or current_date_start,
                    'date_end': current_date_end,
                })
                interval_date_start = False
            else:
                interval_date_start = interval_date_start or current_date_start

        last_version = employee_versions[-1]
        if last_version.job_title:
            current_date_start = max(last_version.date_version, last_version.contract_date_start or date.min)
            res.append({
                'id': last_version.id,
                'job_title': last_version.job_title,
                'date_start': interval_date_start or current_date_start,
                'date_end': last_version.contract_date_end or False,
            })
        elif interval_date_start:
            previous_version = employee_versions[-2]
            res.append({
                'id': previous_version.id,
                'job_title': previous_version.job_title,
                'date_start': interval_date_start,
                'date_end': current_date_start + relativedelta(days=-1),
            })
        return res[::-1]