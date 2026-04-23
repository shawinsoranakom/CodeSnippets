def write(self, vals):
        if vals.get('active') is False:
            # DLE: It should not be necessary to modify this to make work the ORM. The problem was just the recompute
            # of partner.user_ids when you create a new user for this partner, see test test_70_archive_internal_partners
            # You modified it in a previous commit, see original commit of this:
            # https://github.com/odoo/odoo/commit/9d7226371730e73c296bcc68eb1f856f82b0b4ed
            #
            # RCO: when creating a user for partner, the user is automatically added in partner.user_ids.
            # This is wrong if the user is not active, as partner.user_ids only returns active users.
            # Hence this temporary hack until the ORM updates inverse fields correctly.
            self.invalidate_recordset(['user_ids'])
            users = self.env['res.users'].sudo().search([('partner_id', 'in', self.ids)])
            if users:
                if self.env['res.users'].sudo(False).has_access('write'):
                    error_msg = _('You cannot archive contacts linked to an active user.\n'
                                  'You first need to archive their associated user.\n\n'
                                  'Linked active users : %(names)s', names=", ".join([u.display_name for u in users]))
                    action_error = users._action_show()
                    raise RedirectWarning(error_msg, action_error, _('Go to users'))
                else:
                    raise ValidationError(_('You cannot archive contacts linked to an active user.\n'
                                            'Ask an administrator to archive their associated user first.\n\n'
                                            'Linked active users :\n%(names)s', names=", ".join([u.display_name for u in users])))
        if vals.get('website'):
            vals['website'] = self._clean_website(vals['website'])
        if vals.get('parent_id'):
            vals['company_name'] = False
        if vals.get('name'):
            for partner in self:
                for bank in partner.bank_ids:
                    if bank.acc_holder_name == partner.name:
                        bank.acc_holder_name = vals['name']

        # filter to keep only really updated values -> field synchronize goes through
        # partner tree and we should avoid infinite loops in case same value is
        # updated due to cycles. Use case: updating a property field, which updated
        # a computed field, which has an inverse writing the same value on property
        # field. Yay.
        pre_values_list = [{fname: partner[fname] for fname in vals} for partner in self]

        # res.partner must only allow to set the company_id of a partner if it
        # is the same as the company of all users that inherit from this partner
        # (this is to allow the code from res_users to write to the partner!) or
        # if setting the company_id to False (this is compatible with any user
        # company)
        if 'company_id' in vals:
            company_id = vals['company_id']
            for partner in self:
                if company_id and partner.user_ids:
                    company = self.env['res.company'].browse(company_id)
                    companies = set(user.company_id for user in partner.user_ids)
                    if len(companies) > 1 or company not in companies:
                        raise UserError(
                            self.env._("The selected company is not compatible with the companies of the related user(s)"))
                if partner.child_ids:
                    partner.child_ids.write({'company_id': company_id})
        result = True
        # To write in SUPERUSER on field is_company and avoid access rights problems.
        if 'is_company' in vals and not self.env.su and self.env.user.has_group('base.group_partner_manager'):
            result = super(ResPartner, self.sudo()).write({'is_company': vals.get('is_company')})
            del vals['is_company']
        result = result and super().write(vals)
        for partner, pre_values in zip(self, pre_values_list, strict=True):
            if internal_users := partner.user_ids.filtered(lambda u: u._is_internal() and u != self.env.user):
                internal_users.check_access('write')
            updated = {fname: fvalue for fname, fvalue in vals.items() if partner[fname] != pre_values.get(fname)}
            if updated:
                partner._fields_sync(updated)
        return result