def write(self, vals):
        if vals.get('active') and SUPERUSER_ID in self._ids:
            raise UserError(_("You cannot activate the superuser."))
        if vals.get('active') == False and self.env.uid in self._ids:  # noqa: E712
            raise UserError(_("You cannot deactivate the user you're currently logged in as."))

        if vals.get('active'):
            # unarchive partners before unarchiving the users
            self.partner_id.action_unarchive()
        if self == self.env.user:
            writeable = self._self_accessible_fields()[1]
            for key in list(vals):
                if key not in writeable:
                    break
            else:
                if 'company_id' in vals:
                    if vals['company_id'] not in self.env.user.company_ids.ids:
                        del vals['company_id']
                # safe fields only, so we write as super-user to bypass access rights
                self = self.sudo()

        res = super().write(vals)

        if 'company_id' in vals:
            for user in self:
                # if partner is global we keep it that way
                if user.partner_id.company_id and user.partner_id.company_id.id != vals['company_id']:
                    user.partner_id.write({'company_id': user.company_id.id})

        if 'company_id' in vals or 'company_ids' in vals:
            # Reset lazy properties `company` & `companies` on all envs,
            # This is unlikely in a business code to change the company of a user and then do business stuff
            # but in case it happens this is handled.
            # e.g. `account_test_savepoint.py` `setup_company_data`, triggered by `test_account_invoice_report.py`
            for env in list(self.env.transaction.envs):
                if env.user in self:
                    reset_cached_properties(env)

        if 'group_ids' in vals and self.ids:
            # clear caches linked to the users
            self.env['ir.model.access'].call_cache_clearing_methods()

        # per-method / per-model caches have been removed so the various
        # clear_cache/clear_caches methods pretty much just end up calling
        # Registry.clear_cache
        invalidation_fields = self._get_invalidation_fields()
        if invalidation_fields & vals.keys():
            self.env.registry.clear_cache()

        return res