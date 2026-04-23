def write(self, vals):
        trusted_keys = ['active', 'is_correct', 'tag_ids']  # fields where security is checked manually
        if 'forum_id' in vals:
            forum = self.env['forum.forum'].browse(vals['forum_id'])
            forum.check_access('write')
        if 'content' in vals:
            vals['content'] = self._update_content(vals['content'], self.forum_id.id)

        tag_ids = False
        if 'tag_ids' in vals:
            tag_ids = set(self.new({'tag_ids': vals['tag_ids']}).tag_ids.ids)

        for post in self:
            if 'state' in vals:
                if vals['state'] in ['active', 'close']:
                    if not post.can_close:
                        raise AccessError(_('%d karma required to close or reopen a post.', post.karma_close))
                    trusted_keys += ['state', 'closed_uid', 'closed_date', 'closed_reason_id']
                elif vals['state'] == 'flagged':
                    if not post.can_flag:
                        raise AccessError(_('%d karma required to flag a post.', post.forum_id.karma_flag))
                    trusted_keys += ['state', 'flag_user_id']
            if 'active' in vals:
                if not post.can_unlink:
                    raise AccessError(_('%d karma required to delete or reactivate a post.', post.karma_unlink))
            if 'is_correct' in vals:
                if not post.can_accept:
                    raise AccessError(_('%d karma required to accept or refuse an answer.', post.karma_accept))
                # update karma except for self-acceptance
                mult = 1 if vals['is_correct'] else -1
                if vals['is_correct'] != post.is_correct and post.create_uid.id != self.env.uid:
                    post.create_uid.sudo()._add_karma(post.forum_id.karma_gen_answer_accepted * mult, post,
                                                      _('User answer accepted') if mult > 0 else _('Accepted answer removed'))
                    self.env.user.sudo()._add_karma(post.forum_id.karma_gen_answer_accept * mult, post,
                                                    _('Validate an answer') if mult > 0 else _('Remove validated answer'))
            if tag_ids:
                if set(post.tag_ids.ids) != tag_ids and self.env.user.karma < post.forum_id.karma_edit_retag:
                    raise AccessError(_('%d karma required to retag.', post.forum_id.karma_edit_retag))
            if any(key not in trusted_keys for key in vals) and not post.can_edit:
                raise AccessError(_('%d karma required to edit a post.', post.karma_edit))

        res = super().write(vals)

        # if post content modify, notify followers
        if 'content' in vals or 'name' in vals:
            for post in self:
                if post.parent_id:
                    body, subtype_xmlid = _('Answer Edited'), 'website_forum.mt_answer_edit'
                    obj_id = post.parent_id
                else:
                    body, subtype_xmlid = _('Question Edited'), 'website_forum.mt_question_edit'
                    obj_id = post
                obj_id.message_post(body=body, subtype_xmlid=subtype_xmlid)
        if 'active' in vals:
            answers = self.env['forum.post'].with_context(active_test=False).search([('parent_id', 'in', self.ids)])
            if answers:
                answers.write({'active': vals['active']})
        return res