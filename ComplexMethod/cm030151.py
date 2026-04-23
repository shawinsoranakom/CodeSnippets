def __init__(self, completekey='tab', stdin=None, stdout=None, skip=None,
                 nosigint=False, readrc=True, mode=None, backend=None, colorize=False):
        bdb.Bdb.__init__(self, skip=skip, backend=backend if backend else get_default_backend())
        cmd.Cmd.__init__(self, completekey, stdin, stdout)
        sys.audit("pdb.Pdb")
        if stdin is not None and stdin is not sys.stdin:
            self.use_rawinput = False
        self.prompt = '(Pdb) '
        self.aliases = {}
        self.displaying = {}
        self.mainpyfile = ''
        self._wait_for_mainpyfile = False
        self.tb_lineno = {}
        self.mode = mode
        self.colorize = colorize and _colorize.can_colorize(file=stdout or sys.stdout)
        # Try to load readline if it exists
        try:
            import readline
            # remove some common file name delimiters
            readline.set_completer_delims(' \t\n`@#%^&*()=+[{]}\\|;:\'",<>?')
        except ImportError:
            pass

        self.allow_kbdint = False
        self.nosigint = nosigint
        # Consider these characters as part of the command so when the users type
        # c.a or c['a'], it won't be recognized as a c(ontinue) command
        self.identchars = cmd.Cmd.identchars + '=.[](),"\'+-*/%@&|<>~^'

        # Read ~/.pdbrc and ./.pdbrc
        self.rcLines = []
        if readrc:
            home_rcfile = os.path.expanduser("~/.pdbrc")
            local_rcfile = os.path.abspath(".pdbrc")

            try:
                with open(home_rcfile, encoding='utf-8') as rcfile:
                    self.rcLines.extend(rcfile)
            except OSError:
                pass

            if local_rcfile != home_rcfile:
                try:
                    with open(local_rcfile, encoding='utf-8') as rcfile:
                        self.rcLines.extend(rcfile)
                except OSError:
                    pass

        self.commands = {} # associates a command list to breakpoint numbers
        self.commands_defining = False # True while in the process of defining
                                       # a command list
        self.commands_bnum = None # The breakpoint number for which we are
                                  # defining a list

        self.async_shim_frame = None
        self.async_awaitable = None

        self._chained_exceptions = tuple()
        self._chained_exception_index = 0

        self._current_task = None

        self.lineno = None
        self.stack = []
        self.curindex = 0
        self.curframe = None
        self._user_requested_quit = False