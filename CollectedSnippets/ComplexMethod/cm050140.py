def write(self, vals):
        values = vals
        if values.get('body_arch'):
            values['body_arch'] = self._convert_inline_images_to_urls(values['body_arch'])
        if values.get('body_html'):
            values['body_html'] = self._convert_inline_images_to_urls(values['body_html'])
        # If ab_testing is already enabled on a mailing and the campaign is removed, we raise a ValidationError
        if values.get('campaign_id') is False and any(mailing.ab_testing_enabled for mailing in self) and 'ab_testing_enabled' not in values:
            raise ValidationError(_("A campaign should be set when A/B test is enabled"))

        result = super().write(values)
        if values.get('ab_testing_enabled'):
            self._create_ab_testing_utm_campaigns()
        self._fix_attachment_ownership()

        if any(self.mapped('ab_testing_schedule_datetime')):
            schedule_date = min(m.ab_testing_schedule_datetime for m in self if m.ab_testing_schedule_datetime)
            ab_testing_cron = self.env.ref('mass_mailing.ir_cron_mass_mailing_ab_testing').sudo()
            ab_testing_cron._trigger(at=schedule_date)

        return result