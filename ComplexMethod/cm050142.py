def _get_default_ab_testing_campaign_values(self, values=None):
        values = values or dict()
        return {
            'ab_testing_schedule_datetime': values.get('ab_testing_schedule_datetime') or self.ab_testing_schedule_datetime,
            'ab_testing_winner_selection': values.get('ab_testing_winner_selection') or self.ab_testing_winner_selection,
            'mailing_mail_ids': self.ids,
            'name': _('A/B Test: %s', values.get('subject') or self.subject or fields.Datetime.now()),
            'user_id': values.get('user_id') or self.user_id.id or self.env.user.id,
        }