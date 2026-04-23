def checkParam(self, widget, name, value, *, expected=_sentinel,
                   conv=False, eq=None):
        widget[name] = value
        if expected is _sentinel:
            expected = value
            if name in self._clipped:
                if not isinstance(expected, str) and expected < 0:
                    if tk_version >= (8, 7) and name in self._clipped_to_default:
                        expected = self._default_pixels
                    else:
                        expected = 0
        if conv:
            expected = conv(expected)
        if self._stringify or not self.wantobjects:
            if isinstance(expected, tuple):
                expected = tkinter._join(expected)
            else:
                expected = str(expected)
        if eq is None:
            eq = tcl_obj_eq
        self.assertEqual2(widget[name], expected, eq=eq)
        self.assertEqual2(widget.cget(name), expected, eq=eq)
        t = widget.configure(name)
        self.assertEqual(len(t), 5)
        self.assertEqual2(t[4], expected, eq=eq)