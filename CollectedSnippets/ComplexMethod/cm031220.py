def _substitute(self, *args):
        """Internal function."""
        if len(args) != len(self._subst_format): return args
        getboolean = self.tk.getboolean

        getint = self.tk.getint
        def getint_event(s):
            """Tk changed behavior in 8.4.2, returning "??" rather more often."""
            try:
                return getint(s)
            except (ValueError, TclError):
                return s

        if any(isinstance(s, tuple) for s in args):
            args = [s[0] if isinstance(s, tuple) and len(s) == 1 else s
                    for s in args]
        nsign, b, d, f, h, k, s, t, w, x, y, A, E, K, N, W, T, X, Y, D = args
        # Missing: (a, c, m, o, v, B, R)
        e = Event()
        # serial field: valid for all events
        # number of button: ButtonPress and ButtonRelease events only
        # detail: for Enter, Leave, FocusIn, FocusOut and ConfigureRequest
        # events certain fixed strings (see Tcl/Tk documentation)
        # user_data: data string from a virtual event or an empty string
        # height field: Configure, ConfigureRequest, Create,
        # ResizeRequest, and Expose events only
        # keycode field: KeyPress and KeyRelease events only
        # time field: "valid for events that contain a time field"
        # width field: Configure, ConfigureRequest, Create, ResizeRequest,
        # and Expose events only
        # x field: "valid for events that contain an x field"
        # y field: "valid for events that contain a y field"
        # keysym as decimal: KeyPress and KeyRelease events only
        # x_root, y_root fields: ButtonPress, ButtonRelease, KeyPress,
        # KeyRelease, and Motion events
        e.serial = getint(nsign)
        e.num = getint_event(b)
        if T == EventType.VirtualEvent:
            e.user_data = d
            e.detail = '??'
        else:
            e.user_data = '??'
            e.detail = d
        try: e.focus = getboolean(f)
        except TclError: pass
        e.height = getint_event(h)
        e.keycode = getint_event(k)
        e.state = getint_event(s)
        e.time = getint_event(t)
        e.width = getint_event(w)
        e.x = getint_event(x)
        e.y = getint_event(y)
        e.char = A
        try: e.send_event = getboolean(E)
        except TclError: pass
        e.keysym = K
        e.keysym_num = getint_event(N)
        try:
            e.type = EventType(T)
        except ValueError:
            try:
                e.type = EventType(str(T))  # can be int
            except ValueError:
                e.type = T
        try:
            e.widget = self._nametowidget(W)
        except KeyError:
            e.widget = W
        e.x_root = getint_event(X)
        e.y_root = getint_event(Y)
        try:
            e.delta = getint(D)
        except (ValueError, TclError):
            e.delta = 0
        return (e,)