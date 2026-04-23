def interact(self, banner=None, exitmsg=None):
        """Closely emulate the interactive Python console.

        The optional banner argument specifies the banner to print
        before the first interaction; by default it prints a banner
        similar to the one printed by the real Python interpreter,
        followed by the current class name in parentheses (so as not
        to confuse this with the real interpreter -- since it's so
        close!).

        The optional exitmsg argument specifies the exit message
        printed when exiting. Pass the empty string to suppress
        printing an exit message. If exitmsg is not given or None,
        a default message is printed.

        """
        try:
            sys.ps1
            delete_ps1_after = False
        except AttributeError:
            sys.ps1 = ">>> "
            delete_ps1_after = True
        try:
            sys.ps2
            delete_ps2_after = False
        except AttributeError:
            sys.ps2 = "... "
            delete_ps2_after = True

        cprt = 'Type "help", "copyright", "credits" or "license" for more information.'
        if banner is None:
            self.write("Python %s on %s\n%s\n(%s)\n" %
                       (sys.version, sys.platform, cprt,
                        self.__class__.__name__))
        elif banner:
            self.write("%s\n" % str(banner))
        more = 0

        # When the user uses exit() or quit() in their interactive shell
        # they probably just want to exit the created shell, not the whole
        # process. exit and quit in builtins closes sys.stdin which makes
        # it super difficult to restore
        #
        # When self.local_exit is True, we overwrite the builtins so
        # exit() and quit() only raises SystemExit and we can catch that
        # to only exit the interactive shell

        _exit = None
        _quit = None

        if self.local_exit:
            if hasattr(builtins, "exit"):
                _exit = builtins.exit
                builtins.exit = Quitter("exit")

            if hasattr(builtins, "quit"):
                _quit = builtins.quit
                builtins.quit = Quitter("quit")

        try:
            while True:
                try:
                    if more:
                        prompt = sys.ps2
                    else:
                        prompt = sys.ps1
                    try:
                        line = self.raw_input(prompt)
                    except EOFError:
                        self.write("\n")
                        break
                    else:
                        more = self.push(line)
                except KeyboardInterrupt:
                    self.write("\nKeyboardInterrupt\n")
                    self.resetbuffer()
                    more = 0
                except SystemExit as e:
                    if self.local_exit:
                        self.write("\n")
                        break
                    else:
                        raise e
        finally:
            # restore exit and quit in builtins if they were modified
            if _exit is not None:
                builtins.exit = _exit

            if _quit is not None:
                builtins.quit = _quit

            if delete_ps1_after:
                del sys.ps1

            if delete_ps2_after:
                del sys.ps2

            if exitmsg is None:
                self.write('now exiting %s...\n' % self.__class__.__name__)
            elif exitmsg != '':
                self.write('%s\n' % exitmsg)