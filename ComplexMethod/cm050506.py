def _check_hour(self):
        for category in self:
            if category.hour_until and not (0.0 <= category.hour_until <= 24.0):
                raise ValidationError(_('The Availability Until must be set between 00:00 and 24:00'))
            if category.hour_after and not (0.0 <= category.hour_after <= 24.0):
                raise ValidationError(_('The Availability After must be set between 00:00 and 24:00'))
            if category.hour_until and category.hour_after and category.hour_until < category.hour_after:
                raise ValidationError(_('The Availability Until must be greater than Availability After.'))