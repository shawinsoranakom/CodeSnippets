def close(self, reason_id):
        if any(post.parent_id for post in self):
            return False

        reason_offensive = self.env.ref('website_forum.reason_7').id
        reason_spam = self.env.ref('website_forum.reason_8').id
        if reason_id in (reason_offensive, reason_spam):
            for post in self:
                _logger.info('Downvoting user <%s> for posting spam/offensive contents',
                             post.create_uid)
                karma = post.forum_id.karma_gen_answer_flagged
                if reason_id == reason_spam:
                    # If first post, increase the karma to remove
                    count_post = post.search_count([('parent_id', '=', False), ('forum_id', '=', post.forum_id.id), ('create_uid', '=', post.create_uid.id)])
                    if count_post == 1:
                        karma *= 10
                message = (
                    _('Post is closed and marked as spam')
                    if reason_id == reason_spam else
                    _('Post is closed and marked as offensive content')
                )
                post.create_uid.sudo()._add_karma(karma, post, message)

        self.write({
            'state': 'close',
            'closed_uid': self.env.uid,
            'closed_date': datetime.today().strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT),
            'closed_reason_id': reason_id,
        })
        return True