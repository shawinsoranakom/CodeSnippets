def _notify_get_recipients_groups(self, message, model_description, msg_vals=False):
        # Handle project users and managers recipients that can assign
        # tasks and create new one directly from notification emails. Also give
        # access button to portal users and portal customers. If they are notified
        # they should probably have access to the document.
        groups = super()._notify_get_recipients_groups(
            message, model_description, msg_vals=msg_vals
        )
        if not self:
            return groups

        self.ensure_one()

        project_user_group_id = self.env.ref('project.group_project_user').id
        new_group = ('group_project_user', lambda pdata: pdata['type'] == 'user' and project_user_group_id in pdata['groups'], {})
        groups = [new_group] + groups

        if self.project_privacy_visibility in ['invited_users', 'portal']:
            groups.insert(0, (
                'allowed_portal_users',
                lambda pdata: pdata['type'] in ['invited_users', 'portal'],
                {
                    'active': True,
                    'has_button_access': True,
                }
            ))
        portal_privacy = self.project_id.privacy_visibility in ['invited_users', 'portal']
        for group_name, _group_method, group_data in groups:
            if group_name in ('customer', 'user') or group_name == 'portal_customer' and not portal_privacy:
                group_data['has_button_access'] = False
            elif group_name == 'portal_customer' and portal_privacy:
                group_data['has_button_access'] = True

        return groups