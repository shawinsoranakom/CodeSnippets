def make_gui(self):
        """Draw the debugger gui on the screen."""
        pyshell = self.pyshell
        self.flist = pyshell.flist
        self.root = root = pyshell.root
        self.top = top = ListedToplevel(root)
        self.top.wm_title("Debug Control")
        self.top.wm_iconname("Debug")
        top.wm_protocol("WM_DELETE_WINDOW", self.close)
        self.top.bind("<Escape>", self.close)

        self.bframe = bframe = Frame(top)
        self.bframe.pack(anchor="w")
        self.buttons = bl = []

        self.bcont = b = Button(bframe, text="Go", command=self.cont)
        bl.append(b)
        self.bstep = b = Button(bframe, text="Step", command=self.step)
        bl.append(b)
        self.bnext = b = Button(bframe, text="Over", command=self.next)
        bl.append(b)
        self.bret = b = Button(bframe, text="Out", command=self.ret)
        bl.append(b)
        self.bret = b = Button(bframe, text="Quit", command=self.quit)
        bl.append(b)

        for b in bl:
            b.configure(state="disabled")
            b.pack(side="left")

        self.cframe = cframe = Frame(bframe)
        self.cframe.pack(side="left")

        if not self.vstack:
            self.__class__.vstack = BooleanVar(top)
            self.vstack.set(1)
        self.bstack = Checkbutton(cframe,
            text="Stack", command=self.show_stack, variable=self.vstack)
        self.bstack.grid(row=0, column=0)
        if not self.vsource:
            self.__class__.vsource = BooleanVar(top)
        self.bsource = Checkbutton(cframe,
            text="Source", command=self.show_source, variable=self.vsource)
        self.bsource.grid(row=0, column=1)
        if not self.vlocals:
            self.__class__.vlocals = BooleanVar(top)
            self.vlocals.set(1)
        self.blocals = Checkbutton(cframe,
            text="Locals", command=self.show_locals, variable=self.vlocals)
        self.blocals.grid(row=1, column=0)
        if not self.vglobals:
            self.__class__.vglobals = BooleanVar(top)
        self.bglobals = Checkbutton(cframe,
            text="Globals", command=self.show_globals, variable=self.vglobals)
        self.bglobals.grid(row=1, column=1)

        self.status = Label(top, anchor="w")
        self.status.pack(anchor="w")
        self.error = Label(top, anchor="w")
        self.error.pack(anchor="w", fill="x")
        self.errorbg = self.error.cget("background")

        self.fstack = Frame(top, height=1)
        self.fstack.pack(expand=1, fill="both")
        self.flocals = Frame(top)
        self.flocals.pack(expand=1, fill="both")
        self.fglobals = Frame(top, height=1)
        self.fglobals.pack(expand=1, fill="both")

        if self.vstack.get():
            self.show_stack()
        if self.vlocals.get():
            self.show_locals()
        if self.vglobals.get():
            self.show_globals()