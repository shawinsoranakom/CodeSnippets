def _warn_error(self, exception):
        last_error_dt = self.error_datetime
        now = self.env.cr.now().replace(microsecond=0)
        if not last_error_dt or last_error_dt < now - relativedelta(hours=1):
            # message base: event, date
            event, template = self.event_id, self.template_ref
            if self.interval_type == "after_sub":
                scheduled_date = now
            else:
                scheduled_date = self.scheduled_date
            body_content = _(
                "Communication for %(event_name)s scheduled on %(scheduled_date)s failed.",
                event_name=event.name,
                scheduled_date=scheduled_date,
            )

            # add some information on cause
            template_link = Markup('<a href="%s">%s (%s)</a>') % (
                f"{self.get_base_url()}/odoo/{template._name}/{template.id}",
                template.display_name,
                template.id,
            )
            cause = exception.__cause__ or exception.__context__
            if hasattr(cause, 'qweb'):
                source_content = _(
                    "This is due to an error in template %(template_link)s.",
                    template_link=template_link,
                )
                if isinstance(cause, QWebError) and isinstance(cause.__cause__, AttributeError):
                    error_message = _(
                        "There is an issue with dynamic placeholder. Actual error received is: %(error)s.",
                        error=Markup('<br/>%s') % cause.__cause__,
                    )
                else:
                    error_message = _(
                        "Rendering of template failed with error: %(error)s.",
                        error=Markup('<br/>%s') % cause.qweb,
                    )
            else:
                source_content = _(
                    "This may be linked to template %(template_link)s.",
                    template_link=template_link,
                )
                error_message = _(
                    "It failed with error %(error)s.",
                    error=exception_to_unicode(exception),
                )

            body = Markup("<p>%s %s<br /><br />%s</p>") % (body_content, source_content, error_message)
            recipients = (event.organizer_id | event.user_id.partner_id | template.write_uid.partner_id).filtered(
                lambda p: p.active
            )
            self.event_id.message_post(
                body=body,
                force_send=False,  # use email queue, especially it could be cause of error
                notify_author_mention=True,  # in case of event responsible creating attendees
                partner_ids=recipients.ids,
            )
            self.error_datetime = now