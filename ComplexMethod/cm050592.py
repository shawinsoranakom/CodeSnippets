def message_post(self, *, parent_id=False, subtype_id=False, **kwargs):
        """ Temporary workaround to avoid spam. If someone replies on a channel
        through the 'Presentation Published' email, it should be considered as a
        note as we don't want all channel followers to be notified of this answer.
        Also make sure that only one review can be posted per course."""
        self.ensure_one()
        if kwargs.get('message_type') == 'comment' and not self.can_review:
            raise AccessError(_('Not enough karma to review'))
        if parent_id:
            parent_message = self.env['mail.message'].sudo().browse(parent_id)
            if parent_message.subtype_id and parent_message.subtype_id == self.env.ref('website_slides.mt_channel_slide_published'):
                subtype_id = self.env.ref('mail.mt_note').id
        message = super().message_post(parent_id=parent_id, subtype_id=subtype_id, **kwargs)
        if self.env.user._is_internal() and not message.rating_value:
            return message
        if message.subtype_id == self.env.ref("mail.mt_comment"):
            domain = [
                ("res_id", "=", self.id),
                ("author_id", "=", message.author_id.id),
                ("model", "=", "slide.channel"),
                ("subtype_id", "=", self.env.ref("mail.mt_comment").id),
                ("rating_ids", "!=", False),
            ]
            if self.env["mail.message"].search_count(domain, limit=2) > 1:
                raise ValidationError(_("Only a single review can be posted per course."))
        if message.rating_value and message.is_current_user_or_guest_author:
            self.env.user._add_karma(self.karma_gen_channel_rank, self, _("Course Ranked"))
        return message