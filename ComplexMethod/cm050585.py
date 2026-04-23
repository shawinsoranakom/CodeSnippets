def _compute_quiz_info(self, target_partner, quiz_done=False):
        result = dict.fromkeys(self.ids, False)
        slide_partners = self.env['slide.slide.partner'].sudo().search([
            ('slide_id', 'in', self.ids),
            ('partner_id', '=', target_partner.id)
        ])
        slide_partners_map = dict((sp.slide_id.id, sp) for sp in slide_partners)
        for slide in self:
            if not slide.question_ids:
                gains = [0]
            else:
                gains = [slide.quiz_first_attempt_reward,
                         slide.quiz_second_attempt_reward,
                         slide.quiz_third_attempt_reward,
                         slide.quiz_fourth_attempt_reward]
            result[slide.id] = {
                'quiz_karma_max': gains[0],  # what could be gained if succeed at first try
                'quiz_karma_gain': gains[0],  # what would be gained at next test
                'quiz_karma_won': 0,  # what has been gained
                'quiz_attempts_count': 0,  # number of attempts
            }
            slide_partner = slide_partners_map.get(slide.id)
            if slide.question_ids and slide_partner and slide_partner.quiz_attempts_count:
                result[slide.id]['quiz_karma_gain'] = gains[slide_partner.quiz_attempts_count] if slide_partner.quiz_attempts_count < len(gains) else gains[-1]
                result[slide.id]['quiz_attempts_count'] = slide_partner.quiz_attempts_count
                if quiz_done or slide_partner.completed:
                    result[slide.id]['quiz_karma_won'] = gains[slide_partner.quiz_attempts_count-1] if slide_partner.quiz_attempts_count < len(gains) else gains[-1]
        return result