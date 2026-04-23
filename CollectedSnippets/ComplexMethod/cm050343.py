def _add_certification_activity_to_employees(self):
        today = fields.Date.today()
        three_months_later = today + relativedelta(months=3)
        return_val = self.env["mail.activity"]

        jobs_with_certification = self.env["hr.job"].search([("job_skill_ids.is_certification", "=", True)])
        if not jobs_with_certification:
            return return_val

        job_skill_level_mapping = defaultdict(dict)

        for job in jobs_with_certification:
            for cert in job.job_skill_ids.filtered(lambda s: s.is_certification):
                key = (cert.skill_id, cert.skill_level_id)
                summary = f"{cert.skill_id.name}: {cert.skill_level_id.name}"
                job_skill_level_mapping[job][key] = summary

        if not job_skill_level_mapping:
            return return_val

        employee_domain = Domain.AND(
            [
                Domain("job_id", "in", jobs_with_certification.ids),
                Domain.OR(
                    [
                        Domain("user_id", "!=", False),
                        Domain("parent_id.user_id", "!=", False),
                        Domain("job_id.user_id", "!=", False),
                    ],
                ),
            ],
        )
        employees = self.env["hr.employee"].search(employee_domain)
        if not employees:
            return return_val

        emp_skills = self.env["hr.employee.skill"].search(
            Domain.AND(
                [Domain("employee_id", "in", employees.ids), Domain("is_certification", "=", True)],
            ),
        )

        employee_cert_data = defaultdict(dict)
        for es in emp_skills:
            key = (es.skill_id, es.skill_level_id)
            employee_cert_data[es.employee_id][key] = es.valid_to

        existing_activities = self.env["mail.activity"].search(
            Domain.AND(
                [
                    Domain("active", "=", True),
                    Domain("activity_category", "=", "upload_file"),
                    Domain("res_model", "=", "hr.employee"),
                    Domain("res_id", "in", employees.ids),
                ],
            ),
        )
        existing_activity_keys = {(act.res_id, act.summary) for act in existing_activities}

        for employee in employees:
            job_id = employee.job_id
            responsible = employee.user_id or employee.parent_id.user_id or job_id.user_id
            if job_id not in job_skill_level_mapping or not responsible:
                continue

            for skill_level_key, summary in job_skill_level_mapping[job_id].items():
                if (employee.id, summary) in existing_activity_keys:
                    continue

                valid_to_date = employee_cert_data.get(employee, {}).get(skill_level_key)
                if valid_to_date is not None and (valid_to_date is False or valid_to_date > three_months_later):
                    continue

                activity = employee.activity_schedule(
                    act_type_xmlid="hr_skills.mail_activity_data_upload_certification",
                    summary=summary,
                    note="Certification missing or expiring soon",
                    date_deadline=valid_to_date or today,
                    user_id=responsible.id,
                )
                return_val += activity

        return return_val