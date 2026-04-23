def _compute_statistics(self):
        slide_partners = self.env['slide.slide.partner'].sudo().search([('slide_id', 'in', self.slide_id.ids)])
        slide_stats = dict((s.slide_id.id, dict({'attempts_count': 0, 'attempts_unique': 0, 'done_count': 0})) for s in slide_partners)

        for slide_partner in slide_partners:
            slide_stats[slide_partner.slide_id.id]['attempts_count'] += slide_partner.quiz_attempts_count
            slide_stats[slide_partner.slide_id.id]['attempts_unique'] += 1
            if slide_partner.completed:
                slide_stats[slide_partner.slide_id.id]['done_count'] += 1

        for question in self:
            stats = slide_stats.get(question.slide_id.id)
            question.attempts_count = stats.get('attempts_count', 0) if stats else 0
            question.attempts_avg = stats.get('attempts_count', 0) / stats.get('attempts_unique', 1) if stats else 0
            question.done_count = stats.get('done_count', 0) if stats else 0