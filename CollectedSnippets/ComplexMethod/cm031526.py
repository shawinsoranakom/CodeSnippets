def interaction(self, message, frame, info=None):
        self.frame = frame
        self.status.configure(text=message)

        if info:
            type, value, tb = info
            try:
                m1 = type.__name__
            except AttributeError:
                m1 = "%s" % str(type)
            if value is not None:
                try:
                   # TODO redo entire section, tries not needed.
                    m1 = f"{m1}: {value}"
                except:
                    pass
            bg = "yellow"
        else:
            m1 = ""
            tb = None
            bg = self.errorbg
        self.error.configure(text=m1, background=bg)

        sv = self.stackviewer
        if sv:
            stack, i = self.idb.get_stack(self.frame, tb)
            sv.load_stack(stack, i)

        self.show_variables(1)

        if self.vsource.get():
            self.sync_source_line()

        for b in self.buttons:
            b.configure(state="normal")

        self.top.wakeup()
        # Nested main loop: Tkinter's main loop is not reentrant, so use
        # Tcl's vwait facility, which reenters the event loop until an
        # event handler sets the variable we're waiting on.
        self.nesting_level += 1
        self.root.tk.call('vwait', '::idledebugwait')
        self.nesting_level -= 1

        for b in self.buttons:
            b.configure(state="disabled")
        self.status.configure(text="")
        self.error.configure(text="", background=self.errorbg)
        self.frame = None