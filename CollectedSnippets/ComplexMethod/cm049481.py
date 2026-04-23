def reopen(self):
        if any(post.parent_id or post.state != 'close' for post in self):
            return False

        reason_offensive = self.env.ref('website_forum.reason_7')
        reason_spam = self.env.ref('website_forum.reason_8')
        for post in self:
            if post.closed_reason_id in (reason_offensive, reason_spam):
                _logger.info('Upvoting user <%s>, reopening spam/offensive question',
                             post.create_uid)

                karma = post.forum_id.karma_gen_answer_flagged
                if post.closed_reason_id == reason_spam:
                    # If first post, increase the karma to add
                    count_post = post.search_count([('parent_id', '=', False), ('forum_id', '=', post.forum_id.id), ('create_uid', '=', post.create_uid.id)])
                    if count_post == 1:
                        karma *= 10
                post.create_uid.sudo()._add_karma(karma * -1, post, _('Reopen a banned question'))

        self.sudo().write({'state': 'active'})