def _action_done(self, feedback=False, attachment_ids=None):
        """ Private implementation of marking activity as done: posting a message, archiving activity
            (since done), and eventually create the automatical next activity (depending on config).
            :param feedback: optional feedback from user when marking activity as done
            :param attachment_ids: list of ir.attachment ids to attach to the posted mail.message
            :returns (messages, activities) where
                - messages is a recordset of posted mail.message
                - activities is a recordset of mail.activity of forced automically created activities
        """
        # marking as 'done'
        messages = self.env['mail.message']
        next_activities_values = []

        # Search for all attachments linked to the activities we are about to archive. This way, we
        # can link them to the message posted and prevent their disparition. The move is done in
        # sudo to avoid losing inaccessible attachments.
        activity_attachments = self.env['ir.attachment'].sudo().search_fetch([
            ('res_model', '=', self._name),
            ('res_id', 'in', self.ids),
        ], ['res_id']).grouped('res_id')
        attachments_to_remove = self.env['ir.attachment']
        activities_to_remove = self.browse()

        for model, activity_data in self.filtered('res_model')._classify_by_model().items():
            # Allow user without access to the record to "mark as done" activities assigned to them. At the end of the
            # method, the activity is archived which ensure the user has enough right on the activities.
            records_sudo = self.env[model].sudo().browse(activity_data['record_ids'])
            existing = records_sudo.exists()  # in case record was cascade-deleted in DB, skipping unlink override
            for record_sudo, activity in zip(records_sudo, activity_data['activities']):
                # extract value to generate next activities
                if activity.chaining_type == 'trigger':
                    vals = activity.with_context(activity_previous_deadline=activity.date_deadline)._prepare_next_activity_values()
                    next_activities_values.append(vals)

                # post message on activity, before deleting it

                if record_sudo in existing:
                    activity_message = record_sudo.message_post_with_source(
                        'mail.message_activity_done',
                        attachment_ids=attachment_ids,
                        author_id=self.env.user.partner_id.id,
                        render_values={
                            'activity': activity,
                            'feedback': feedback,
                            'display_assignee': activity.user_id != self.env.user
                        },
                        mail_activity_type_id=activity.activity_type_id.id,
                        subtype_xmlid='mail.mt_activities',
                    )
                else:
                    activity_message = self.env['mail.message']
                    activities_to_remove += activity
                if attachment_ids:
                    activity.attachment_ids = attachment_ids

                # Moving the attachments in the message
                # TODO: Fix void res_id on attachment when you create an activity with an image
                # directly, see route /web_editor/attachment/add
                message_attachments = activity_attachments.get(activity.id)
                if message_attachments and activity_message:
                    message_attachments.write({
                        'res_id': activity_message.id,
                        'res_model': activity_message._name,
                    })
                    activity_message.attachment_ids = message_attachments
                # removing attachments linked to activity if record is missing
                elif message_attachments:
                    attachments_to_remove += message_attachments
                messages += activity_message

        next_activities = self.env['mail.activity']
        if next_activities_values:
            next_activities = self.env['mail.activity'].create(next_activities_values)

        # remove lost activities and attachments, not actionnable anyway anymore
        if attachments_to_remove:
            attachments_to_remove.unlink()
        if activities_to_remove:
            activities_to_remove.unlink()

        # once done, archive to keep history without keeping them alive
        (self - activities_to_remove).action_archive()
        if feedback:
            (self - activities_to_remove).feedback = feedback
        return messages, next_activities