def _compute_account_audit_log_preview(self):
        audit_messages = self.filtered(lambda m: m.message_type == 'notification')
        (self - audit_messages).account_audit_log_preview = False
        for message in audit_messages:
            title = message.subject or message.preview
            tracking_value_ids = message.sudo().tracking_value_ids._filter_has_field_access(self.env)
            if not title and tracking_value_ids:
                title = self.env._("Updated")
            if not title and message.subtype_id and not message.subtype_id.internal:
                title = message.subtype_id.display_name
            audit_log_preview = (title or '') + '\n'
            audit_log_preview += "\n".join(
                "%(old_value)s ⇨ %(new_value)s (%(field)s)" % {
                    'old_value': fmt_vals['oldValue'],
                    'new_value': fmt_vals['newValue'],
                    'field': fmt_vals['fieldInfo']['changedField'],
                }
                for fmt_vals in tracking_value_ids._tracking_value_format()
            )
            message.account_audit_log_preview = audit_log_preview