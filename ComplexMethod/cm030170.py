def do_quit(self, arg):
        """q(uit) | exit

        Quit from the debugger. The program being executed is aborted.
        """
        # Show prompt to kill process when in 'inline' mode and if pdb was not
        # started from an interactive console. The attribute sys.ps1 is only
        # defined if the interpreter is in interactive mode.
        if self.mode == 'inline' and not hasattr(sys, 'ps1'):
            while True:
                try:
                    reply = input('Quitting pdb will kill the process. Quit anyway? [y/n] ')
                    reply = reply.lower().strip()
                except EOFError:
                    reply = 'y'
                    self.message('')
                if reply == 'y' or reply == '':
                    sys.exit(1)
                elif reply.lower() == 'n':
                    return

        self._user_requested_quit = True
        self.set_quit()
        return 1