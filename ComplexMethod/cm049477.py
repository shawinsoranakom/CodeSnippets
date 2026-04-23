def _compute_post_karma_rights(self):
        user = self.env.user
        is_admin = self.env.is_admin()
        # sudoed recordset instead of individual posts so values can be
        # prefetched in bulk
        for post, post_sudo in zip(self, self.sudo()):
            is_creator = post.create_uid == user

            post.karma_accept = post.forum_id.karma_answer_accept_own if post.parent_id.create_uid == user else post.forum_id.karma_answer_accept_all
            post.karma_edit = post.forum_id.karma_edit_own if is_creator else post.forum_id.karma_edit_all
            post.karma_close = post.forum_id.karma_close_own if is_creator else post.forum_id.karma_close_all
            post.karma_unlink = post.forum_id.karma_unlink_own if is_creator else post.forum_id.karma_unlink_all
            post.karma_comment = post.forum_id.karma_comment_own if is_creator else post.forum_id.karma_comment_all
            post.karma_comment_convert = post.forum_id.karma_comment_convert_own if is_creator else post.forum_id.karma_comment_convert_all
            post.karma_flag = post.forum_id.karma_flag

            post.can_ask = is_admin or user.karma >= post.forum_id.karma_ask
            post.can_answer = is_admin or user.karma >= post.forum_id.karma_answer
            post.can_accept = is_admin or user.karma >= post.karma_accept
            post.can_edit = is_admin or user.karma >= post.karma_edit
            post.can_close = is_admin or user.karma >= post.karma_close
            post.can_unlink = is_admin or user.karma >= post.karma_unlink
            post.can_upvote = is_admin or user.karma >= post.forum_id.karma_upvote or post.user_vote == -1
            post.can_downvote = is_admin or user.karma >= post.forum_id.karma_downvote or post.user_vote == 1
            post.can_comment = is_admin or user.karma >= post.karma_comment
            post.can_comment_convert = is_admin or user.karma >= post.karma_comment_convert
            post.can_view = post.can_close or post_sudo.active and (post_sudo.create_uid.karma > 0 or post_sudo.create_uid == user)
            post.can_display_biography = is_admin or (post_sudo.create_uid.karma >= post.forum_id.karma_user_bio and post_sudo.create_uid.website_published)
            post.can_post = is_admin or user.karma >= post.forum_id.karma_post
            post.can_flag = is_admin or user.karma >= post.forum_id.karma_flag
            post.can_moderate = is_admin or user.karma >= post.forum_id.karma_moderate
            post.can_use_full_editor = is_admin or user.karma >= post.forum_id.karma_editor