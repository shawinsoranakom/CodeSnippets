def P(self):
        """
        Time, in 12-hour hours, minutes and 'a.m.'/'p.m.', with minutes left
        off if they're zero and the strings 'midnight' and 'noon' if
        appropriate. Examples: '1 a.m.', '1:30 p.m.', 'midnight', 'noon',
        '12:30 p.m.' Proprietary extension.
        """
        if self.data.minute == 0 and self.data.hour == 0:
            return _("midnight")
        if self.data.minute == 0 and self.data.hour == 12:
            return _("noon")
        return "%s %s" % (self.f(), self.a())