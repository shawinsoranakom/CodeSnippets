def employees_infos(self, token, limit, offset, domain):
        for condition in domain:
            if not isinstance(condition, (list, tuple)) or len(condition) != 3:
                continue
            field_name, operator, _value = condition  # Force '&' implicit syntax
            if field_name not in ('name', 'department_id') or operator not in ('=', 'ilike'):
                raise UserError(_(
                    "Invalid domain, use 'name' and/or 'department_id' fields "
                    "with '=' and/or 'ilike' operators.",
                ))

        company = self._get_company(token)
        if company:
            domain = Domain(domain) & Domain('company_id', '=', company.id)
            employees = request.env['hr.employee'].sudo().search_fetch(domain, ['id', 'display_name', 'job_id'],
                limit=limit, offset=offset, order="name, id")
            employees_data = [{
                'id': employee.id,
                'display_name': employee.display_name,
                'job_id': employee.job_id.name,
                'avatar': image_data_uri(employee.avatar_128),
                'status': employee.attendance_state,
                'mode': employee.last_attendance_id.in_mode
            } for employee in employees]
            return {'records': employees_data, 'length': request.env['hr.employee'].sudo().search_count(domain)}
        return []