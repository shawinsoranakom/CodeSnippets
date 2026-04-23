def convert_comment_to_answer(self, message_id):
        """ Tool to convert a comment (mail.message) into an answer (forum.post).
        The original comment is unlinked and a new answer from the comment's author
        is created. Nothing is done if the comment's author already answered the
        question. """
        comment_sudo = self.env['mail.message'].sudo().browse(message_id)
        post = self.browse(comment_sudo.res_id)
        if not comment_sudo.author_id or not comment_sudo.author_id.user_ids:  # only comment posted by users can be converted
            return False

        # karma-based action check: must check the message's author to know if own / all
        is_author = comment_sudo.author_id.id == self.env.user.partner_id.id
        karma_own = post.forum_id.karma_comment_convert_own
        karma_all = post.forum_id.karma_comment_convert_all
        karma_convert = is_author and karma_own or karma_all
        can_convert = self.env.user.karma >= karma_convert
        if not can_convert:
            if is_author and karma_own < karma_all:
                raise AccessError(_('%d karma required to convert your comment to an answer.', karma_own))
            else:
                raise AccessError(_('%d karma required to convert a comment to an answer.', karma_all))

        # check the message's author has not already an answer
        question = post.parent_id if post.parent_id else post
        post_create_uid = comment_sudo.author_id.user_ids[0]
        if any(answer.create_uid.id == post_create_uid.id for answer in question.child_ids):
            return False

        # create the new post
        post_values = {
            'forum_id': question.forum_id.id,
            'content': comment_sudo.body,
            'parent_id': question.id,
            'name': _('Re: %s', question.name or ''),
        }
        # done with the author user to have create_uid correctly set
        new_post = self.with_user(post_create_uid).sudo().create(post_values).sudo(False)

        # delete comment
        comment_sudo.unlink()

        return new_post