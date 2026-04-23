def _check_action_id(self):
        action_open_website = self.env.ref('base.action_open_website', raise_if_not_found=False)
        if action_open_website and any(user.action_id.id == action_open_website.id for user in self):
            raise ValidationError(_('The "App Switcher" action cannot be selected as home action.'))
        # We use sudo() because  "Access rights" admins can't read action models
        for user in self.sudo():
            if user.action_id.type == "ir.actions.client":
                # Prevent using reload actions.
                action = self.env["ir.actions.client"].browse(user.action_id.id)  # magic
                if action.tag == "reload":
                    raise ValidationError(_('The "%s" action cannot be selected as home action.', action.name))

            elif user.action_id.type == "ir.actions.act_window":
                # Restrict actions that include 'active_id' in their context.
                action = self.env["ir.actions.act_window"].browse(user.action_id.id)  # magic
                if not action.context:
                    continue
                if "active_id" in action.context:
                    raise ValidationError(
                        _('The action "%s" cannot be set as the home action because it requires a record to be selected beforehand.', action.name)
                    )