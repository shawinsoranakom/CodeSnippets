def _get_access_action(self, access_uid=None, force_website=False):
        """ Instead of the classic form view, redirect to the online document for
        portal users or if force_website=True. """
        self.ensure_one()

        user, record = self.env.user, self
        if access_uid:
            try:
                record.check_access('read')
            except exceptions.AccessError:
                return super(PortalMixin, self)._get_access_action(
                    access_uid=access_uid, force_website=force_website
                )
            user = self.env['res.users'].sudo().browse(access_uid)
            record = self.with_user(user)
        if user.share or force_website:
            try:
                record.check_access('read')
            except exceptions.AccessError:
                if force_website:
                    return {
                        'type': 'ir.actions.act_url',
                        'url': record.access_url,
                        'target': 'self',
                        'res_id': record.id,
                    }
                else:
                    pass
            else:
                return {
                    'type': 'ir.actions.act_url',
                    'url': record._get_share_url(),
                    'target': 'self',
                    'res_id': record.id,
                }
        return super(PortalMixin, self)._get_access_action(
            access_uid=access_uid, force_website=force_website
        )