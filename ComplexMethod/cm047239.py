def _unlink_except_master_data(self):
        portal_user_template = self.env.ref('base.template_portal_user_id', False)
        public_user = self.env.ref('base.public_user', False)
        if SUPERUSER_ID in self.ids:
            raise UserError(_('You can not remove the admin user as it is used internally for resources created by Odoo (updates, module installation, ...)'))
        user_admin = self.env.ref('base.user_admin', raise_if_not_found=False)
        if user_admin and user_admin in self:
            raise UserError(_('You cannot delete the admin user because it is utilized in various places (such as security configurations,...). Instead, archive it.'))
        self.env.registry.clear_cache()
        if portal_user_template and portal_user_template in self:
            raise UserError(_('Deleting the template users is not allowed. Deleting this profile will compromise critical functionalities.'))
        if public_user and public_user in self:
            raise UserError(_("Deleting the public user is not allowed. Deleting this profile will compromise critical functionalities."))