def write(self, vals):
        if not (self.env.su or self.env.user.has_group('base.group_user')):
            vals.pop('author_id', None)
            vals.pop('email_from', None)
        record_changed = 'model' in vals or 'res_id' in vals
        if record_changed and not self.env.is_system():
            raise AccessError(_("Only administrators can modify 'model' and 'res_id' fields."))
        if record_changed or 'message_type' in vals:
            self._invalidate_documents()
        res = super().write(vals)
        if vals.get('attachment_ids'):
            self.attachment_ids.check_access('read')
        if 'notification_ids' in vals or record_changed:
            self._invalidate_documents()
        return res