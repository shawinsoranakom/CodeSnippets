def cmdloop(self, intro=None):
        self.preloop()
        if intro is not None:
            self.intro = intro
        if self.intro:
            self.message(str(self.intro))
        stop = None
        while not stop:
            if self._interact_state is not None:
                try:
                    reply = self._get_input(prompt=">>> ", state="interact")
                except KeyboardInterrupt:
                    # Match how KeyboardInterrupt is handled in a REPL
                    self.message("\nKeyboardInterrupt")
                except EOFError:
                    self.message("\n*exit from pdb interact command*")
                    self._interact_state = None
                else:
                    self._run_in_python_repl(reply)
                continue

            if not self.cmdqueue:
                try:
                    state = "commands" if self.commands_defining else "pdb"
                    reply = self._get_input(prompt=self.prompt, state=state)
                except EOFError:
                    reply = "EOF"

                self.cmdqueue.append(reply)

            line = self.cmdqueue.pop(0)
            line = self.precmd(line)
            stop = self.onecmd(line)
            stop = self.postcmd(stop, line)
        self.postloop()