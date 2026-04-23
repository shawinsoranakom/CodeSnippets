def create(self, vals_list):
        vals_per_company = defaultdict(list)
        for idx, vals in enumerate(vals_list):
            if vals.get('user_id'):
                user = self.env['res.users'].browse(vals['user_id'])
                vals.update(self._sync_user(user, bool(vals.get('image_1920'))))
                vals['name'] = vals.get('name', user.name)
                self._remove_work_contact_id(user, vals.get('company_id'))
            # Having one create per company is necessary to pass the company in the context to correctly set it in
            # the underlying version created by the framework
            vals_per_company[vals.get('company_id', self.env.company)].append((idx, vals))
        index_per_employee = {}
        employees = self.env['hr.employee']
        for company, vals_list in vals_per_company.items():
            idxs, vals_list = zip(*vals_list)
            new_employees = super(HrEmployee, self.with_company(company)).create(vals_list)
            index_per_employee.update(dict(zip(new_employees, idxs)))
            employees |= new_employees
        # As we do a custom batch by company, we must reorder the records to respect the original order.
        employees = employees.sorted(key=lambda employee: index_per_employee[employee])
        # Sudo in case HR officer doesn't have the Contact Creation group
        employees.filtered(lambda e: not e.work_contact_id).sudo()._create_work_contacts()
        if self.env.context.get('salary_simulation'):
            return employees
        for employee_sudo in employees.sudo():
            # creating 'svg/xml' attachments requires specific rights
            if not employee_sudo.image_1920 and self.env['ir.ui.view'].sudo(False).has_access('write'):
                employee_sudo.image_1920 = employee_sudo._avatar_generate_svg()
                employee_sudo.work_contact_id.image_1920 = employee_sudo.image_1920
        employee_departments = employees.department_id
        if employee_departments:
            self.env['discuss.channel'].sudo().search([
                ('subscription_department_ids', 'in', employee_departments.ids)
            ])._subscribe_users_automatically()
        onboarding_notes_bodies = {}
        hr_root_menu = self.env.ref('hr.menu_hr_root')
        for employee in employees:
            # Launch onboarding plans
            url = '/odoo/%s/action-hr.plan_wizard_action?active_model=hr.employee&menu_id=%s' % (employee.id, hr_root_menu.id)
            onboarding_notes_bodies[employee.id] = Markup(_(
                '<b>Congratulations!</b> May I recommend you to setup an <a href="%s">onboarding plan?</a>',
            )) % url
        employees._message_log_batch(onboarding_notes_bodies)
        employees.invalidate_recordset()
        return employees