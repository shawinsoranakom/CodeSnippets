def create(self, vals_list):
        defaults_to_check = self.default_get(['content', 'forum_id'])
        for vals in vals_list:
            content = vals.get('content', defaults_to_check.get('content'))
            if content:
                forum_id = vals.get('forum_id', defaults_to_check.get('forum_id'))
                vals['content'] = self._update_content(content, forum_id)

        posts = super(ForumPost, self.with_context(mail_create_nolog=True)).create(vals_list)

        for post in posts:
            # deleted or closed questions
            if post.parent_id and (post.parent_id.state == 'close' or post.parent_id.active is False):
                raise UserError(_('Posting answer on a [Deleted] or [Closed] question is not possible.'))
            # karma-based access
            if not post.parent_id and not post.can_ask:
                raise AccessError(_('%d karma required to create a new question.', post.forum_id.karma_ask))
            elif post.parent_id and not post.can_answer:
                raise AccessError(_('%d karma required to answer a question.', post.forum_id.karma_answer))
            if not post.parent_id and not post.can_post:
                post.sudo().state = 'pending'

            # add karma for posting new questions
            if not post.parent_id and post.state == 'active':
                post.create_uid.sudo()._add_karma(post.forum_id.karma_gen_question_new, post, _('Ask a new question'))
        posts.sudo()._notify_state_update()
        return posts