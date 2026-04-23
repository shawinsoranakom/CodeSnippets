def create(self, vals_list):
        for vals in vals_list:
            self._handle_create_write(vals)

            if 'user_id' not in vals:
                company = self.env['res.company'].browse(vals.get('company_id'))
                vals['user_id'] = company._get_public_user().id if company else self.env.ref('base.public_user').id

        websites = super().create(vals_list)
        websites.company_id._compute_website_id()
        for website in websites:
            website._bootstrap_homepage()

        if not self.env.user.has_group('website.group_multi_website') and self.search_count([]) > 1:
            all_user_groups = 'base.group_portal,base.group_user,base.group_public'
            groups = self.env['res.groups'].concat(*(self.env.ref(it) for it in all_user_groups.split(',')))
            groups.write({'implied_ids': [(4, self.env.ref('website.group_multi_website').id)]})

        return websites