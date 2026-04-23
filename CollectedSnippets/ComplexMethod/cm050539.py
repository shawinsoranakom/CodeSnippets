def _get_access_action(self, access_uid=None, force_website=False):
        self.ensure_one()
        user = self.env['res.users'].sudo().browse(access_uid) if access_uid else self.env.user
        if (
            user
            and user._is_portal()
            and self.with_user(user).has_access('read')
            and self.project_id
            and self.project_id.with_user(user).has_access('read')
            and self.project_id._check_project_sharing_access()
        ):
            return {
                'type': 'ir.actions.act_url',
                'url': f'/my/projects/{self.project_id.id}/project_sharing/{self.id}',
                'target': 'self',
            }
        return super()._get_access_action(access_uid, force_website)