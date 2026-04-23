def __init__(self, flist=None):
        ms = self.menu_specs
        if ms[2][0] != "shell":
            ms.insert(2, ("shell", "She_ll"))
        self.interp = ModifiedInterpreter(self)
        if flist is None:
            root = Tk()
            fixwordbreaks(root)
            root.withdraw()
            flist = PyShellFileList(root)

        self.shell_sidebar = None  # initialized below

        OutputWindow.__init__(self, flist, None, None)

        self.usetabs = False
        # indentwidth must be 8 when using tabs.  See note in EditorWindow:
        self.indentwidth = 4

        self.sys_ps1 = sys.ps1 if hasattr(sys, 'ps1') else '>>>\n'
        self.prompt_last_line = self.sys_ps1.split('\n')[-1]
        self.prompt = self.sys_ps1  # Changes when debug active

        text = self.text
        text.configure(wrap="char")
        text.bind("<<newline-and-indent>>", self.enter_callback)
        text.bind("<<plain-newline-and-indent>>", self.linefeed_callback)
        text.bind("<<interrupt-execution>>", self.cancel_callback)
        text.bind("<<end-of-file>>", self.eof_callback)
        text.bind("<<open-stack-viewer>>", self.open_stack_viewer)
        text.bind("<<toggle-debugger>>", self.toggle_debugger)
        text.bind("<<toggle-jit-stack-viewer>>", self.toggle_jit_stack_viewer)
        text.bind("<<copy-with-prompts>>", self.copy_with_prompts_callback)
        if use_subprocess:
            text.bind("<<view-restart>>", self.view_restart_mark)
            text.bind("<<restart-shell>>", self.restart_shell)
        self.squeezer = self.Squeezer(self)
        text.bind("<<squeeze-current-text>>",
                  self.squeeze_current_text_event)

        self.save_stdout = sys.stdout
        self.save_stderr = sys.stderr
        self.save_stdin = sys.stdin
        from idlelib import iomenu
        self.stdin = StdInputFile(self, "stdin",
                                  iomenu.encoding, iomenu.errors)
        self.stdout = StdOutputFile(self, "stdout",
                                    iomenu.encoding, iomenu.errors)
        self.stderr = StdOutputFile(self, "stderr",
                                    iomenu.encoding, "backslashreplace")
        self.console = StdOutputFile(self, "console",
                                     iomenu.encoding, iomenu.errors)
        if not use_subprocess:
            sys.stdout = self.stdout
            sys.stderr = self.stderr
            sys.stdin = self.stdin
        try:
            # page help() text to shell.
            import pydoc # import must be done here to capture i/o rebinding.
            # XXX KBK 27Dec07 use text viewer someday, but must work w/o subproc
            pydoc.pager = pydoc.plainpager
        except:
            sys.stderr = sys.__stderr__
            raise
        #
        self.history = self.History(self.text)
        #
        self.pollinterval = 50  # millisec

        self.shell_sidebar = self.ShellSidebar(self)

        # Insert UserInputTaggingDelegator at the top of the percolator,
        # but make calls to text.insert() skip it.  This causes only insert
        # events generated in Tcl/Tk to go through this delegator.
        self.text.insert = self.per.top.insert
        self.per.insertfilter(UserInputTaggingDelegator())

        if not use_subprocess:
            # Menu options "View Last Restart" and "Restart Shell" are disabled
            self.update_menu_state("shell", 0, "disabled")
            self.update_menu_state("shell", 1, "disabled")