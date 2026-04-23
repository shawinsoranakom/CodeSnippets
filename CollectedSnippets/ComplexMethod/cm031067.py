def checkEnumParam(self, widget, name, *values,
                       errmsg=None, allow_empty=False, fullname=None,
                       sort=False, **kwargs):
        self.checkParams(widget, name, *values, **kwargs)
        if errmsg is None:
            if sort:
                if values[-1]:
                    values = tuple(sorted(values))
                else:
                    values = tuple(sorted(values[:-1])) + ('',)
            errmsg2 = ' %s "{}": must be %s%s or %s' % (
                    fullname or name,
                    ', '.join(values[:-1]),
                    ',' if len(values) > 2 else '',
                    values[-1] or '""')
            if '' not in values and not allow_empty:
                self.checkInvalidParam(widget, name, '',
                                       errmsg='ambiguous' + errmsg2)
            errmsg = 'bad' + errmsg2
        self.checkInvalidParam(widget, name, 'spam', errmsg=errmsg)