def _action_set_quiz_done(self, completed=True):
        """Add or remove karma point related to the quiz.

        :param completed:
            True if the quiz will be marked as completed (karma will be increased)
            If set to False, we will remove the karma instead of increasing it,
            so that the user can take the quiz multiple times but not gain karma infinitely
        """
        if any(not slide.channel_id.is_member or not slide.website_published for slide in self):
            raise UserError(
                _('You cannot mark a slide quiz as completed if you are not among its members or it is unpublished.') if completed
                else _('You cannot mark a slide quiz as not completed if you are not among its members or it is unpublished.')
            )

        points = 0
        for slide in self:
            user_membership_sudo = slide.user_membership_id.sudo()
            if not user_membership_sudo \
               or user_membership_sudo.completed == completed \
               or not user_membership_sudo.quiz_attempts_count \
               or not slide.question_ids:
                continue

            gains = [slide.quiz_first_attempt_reward,
                     slide.quiz_second_attempt_reward,
                     slide.quiz_third_attempt_reward,
                     slide.quiz_fourth_attempt_reward]
            points = gains[min(user_membership_sudo.quiz_attempts_count, len(gains)) - 1]
            if points:
                if completed:
                    reason = _('Quiz Completed')
                else:
                    points *= -1
                    reason = _('Quiz Set Uncompleted')
                self.env.user.sudo()._add_karma(points, slide, reason)

        return True