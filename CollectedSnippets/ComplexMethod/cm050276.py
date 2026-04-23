def write(self, vals):
        if 'work_contact_id' in vals:
            self.message_unsubscribe(self.work_contact_id.ids)
        if 'user_id' in vals:
            # Update the profile pictures with user, except if provided
            user = self.env['res.users'].browse(vals['user_id'])
            vals.update(self._sync_user(user, (bool(all(emp.image_1920 for emp in self)))))
            self._remove_work_contact_id(user, vals.get('company_id'))
        if 'work_permit_expiration_date' in vals:
            vals['work_permit_scheduled_activity'] = False
        if vals.get('tz'):
            users_to_update = self.env['res.users']
            for employee in self:
                if employee.user_id and employee.company_id == employee.user_id.company_id and vals['tz'] != employee.user_id.tz:
                    users_to_update |= employee.user_id
            if users_to_update:
                users_to_update.write({'tz': vals['tz']})
        if vals.get('department_id') or vals.get('user_id'):
            department_id = vals['department_id'] if vals.get('department_id') else self[:1].department_id.id
            # When added to a department or changing user, subscribe to the channels auto-subscribed by department
            self.env['discuss.channel'].sudo().search([
                ('subscription_department_ids', 'in', department_id)
            ])._subscribe_users_automatically()
        if vals.get('departure_description'):
            for employee in self:
                employee.message_post(body=_(
                    'Additional Information: \n %(description)s',
                    description=vals.get('departure_description')))
        # Only one write call for all the fields from hr.version
        new_vals = vals.copy()
        version_vals = {val: new_vals.pop(val) for val in vals if val in self._fields and self._fields[val].inherited}
        res = super().write(new_vals)
        if 'work_contact_id' in vals:
            account_ids = self.bank_account_ids.ids
            if account_ids:
                bank_accounts = self.env['res.partner.bank'].sudo().browse(account_ids)
                for bank_account in bank_accounts:
                    if vals['work_contact_id'] != bank_account.partner_id.id:
                        if bank_account.allow_out_payment:
                            bank_account.allow_out_payment = False
                        if vals['work_contact_id']:
                            bank_account.partner_id = vals['work_contact_id']
        if version_vals:
            version_vals['last_modified_date'] = fields.Datetime.now()
            version_vals['last_modified_uid'] = self.env.uid
            self.version_id.write(version_vals)

            for employee in self:
                employee._track_set_log_message(Markup("<b>Modified on the Version '%s'</b>") % employee.version_id.display_name)
        if res and 'resource_calendar_id' in vals:
            resources_per_calendar_id = defaultdict(lambda: self.env['resource.resource'])
            for employee in self:
                if employee.version_id == employee.current_version_id:
                    resources_per_calendar_id[employee.resource_calendar_id.id] += employee.resource_id
            for calendar_id, resources in resources_per_calendar_id.items():
                resources.write({'calendar_id': calendar_id})
        return res