def _onchange_format(self):
        warning = {
            'warning': {
                'title': _("Using 24-hour clock format with AM/PM can cause issues."),
                'message': _("Changing to 12-hour clock format instead."),
                'type': 'notification'
            }
        }
        for lang in self:
            if lang.date_format and "%H" in lang.date_format and "%p" in lang.date_format:
                lang.date_format = lang.date_format.replace("%H", "%I")
                return warning
            if lang.time_format and "%H" in lang.time_format and "%p" in lang.time_format:
                lang.time_format = lang.time_format.replace("%H", "%I")
                return warning