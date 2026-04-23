def _get_with_access(self, message_id, mode="read", **kwargs):
        message = self.browse(message_id).exists()
        if not message:
            return message

        # sanity check on kwargs
        allowed_params = self.env[message.sudo().model or 'mail.thread']._get_allowed_access_params()
        if invalid := (set((kwargs or {}).keys()) - allowed_params):
            _logger.warning("Invalid parameters to _get_with_access: %s", invalid)

        if self.env.user._is_public() and self.env["mail.guest"]._get_guest_from_context():
            # Don't check_access_rights for public user with a guest, as the rules are
            # incorrect due to historically having no reason to allow operations on messages to
            # public user before the introduction of guests. Even with ignoring the rights,
            # check_access_rule and its sub methods are already covering all the cases properly.
            if not message.sudo(False)._get_forbidden_access(mode):
                return message
        else:
            if message.sudo(False).has_access(mode):
                return message

        if message.model and message.res_id:
            thread_su = self.env[message.model].browse(message.res_id).sudo()
            access_mode = thread_su._mail_get_operation_for_mail_message_operation(mode)[thread_su]
            if access_mode and self.env[message.model]._get_thread_with_access(message.res_id, mode=access_mode, **kwargs):
                return message

        return self.browse()