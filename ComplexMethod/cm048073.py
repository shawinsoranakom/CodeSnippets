def _force_cancel(self, reason=None, msg_subtype='mail.mt_comment', notify_responsibles=True):
        leaves = self.browse() if self.env.context.get(MODULE_UNINSTALL_FLAG) else self
        if reason:
            model_description = self.env['ir.model']._get('hr.holidays').display_name
            for leave in leaves:
                body = self.env._(
                    "The time off request has been cancelled for the following reason:%(reason)s",
                    reason=Markup("<p>{reason}</p>").format(reason=reason)
                )
                leave.message_post(
                    body=body,
                    subtype_xmlid=msg_subtype
                )

                if not notify_responsibles:
                    continue

                responsibles = self.env['res.partner']
                # manager
                if (leave.holiday_status_id.leave_validation_type == 'manager' and leave.state == 'validate') or (leave.holiday_status_id.leave_validation_type == 'both' and leave.state == 'validate1'):
                    responsibles = leave.employee_id.leave_manager_id.partner_id
                # officer
                elif leave.holiday_status_id.leave_validation_type == 'hr' and leave.state == 'validate':
                    responsibles = leave.holiday_status_id.responsible_ids.partner_id
                # both
                elif leave.holiday_status_id.leave_validation_type == 'both' and leave.state == 'validate':
                    responsibles = leave.employee_id.leave_manager_id.partner_id
                    responsibles |= leave.holiday_status_id.responsible_ids.partner_id

                if responsibles:
                    body = self.env._(
                        "%(leave_name)s has been cancelled for the following reason: %(reason)s",
                        leave_name=leave.display_name,
                        reason=Markup("<blockquote>{reason}</blockquote>").format(reason=reason),
                    )
                    leave.message_notify(
                        partner_ids=responsibles.ids,
                        model_description=model_description,
                        subject=self.env._('Cancelled Time Off'),
                        body=body,
                        email_layout_xmlid="mail.mail_notification_layout",
                        subtitles=[leave.display_name],
                    )
        leave_sudo = self.sudo()
        leave_sudo.state = "cancel"
        leave_sudo.activity_update()
        leave_sudo._post_leave_cancel()