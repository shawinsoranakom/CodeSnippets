def checkPixelsParam(self, widget, name, *values, conv=None, **kwargs):
        if conv is None:
            if self._rounds_pixels and name not in self._no_round:
                conv = round
        alow_neg = tk_version < (9, 1)
        for value in values:
            expected = _sentinel
            conv1 = conv
            if isinstance(value, str):
                if not getattr(self, '_converts_pixels', True):
                    conv1 = str
                if conv1 and conv1 is not str:
                    expected = pixels_conv(value) * self.scaling
                    conv1 = round
            elif not alow_neg and isinstance(value, (int, float)) and value < 0:
                self.checkInvalidParam(widget, name, value)
                continue
            self.checkParam(widget, name, value, expected=expected,
                            conv=conv1, **kwargs)
        errmsg = '(bad|expected) screen distance ((or "" )?but got )?"{}"'
        self.checkInvalidParam(widget, name, '6x', errmsg=errmsg)
        self.checkInvalidParam(widget, name, 'spam', errmsg=errmsg)