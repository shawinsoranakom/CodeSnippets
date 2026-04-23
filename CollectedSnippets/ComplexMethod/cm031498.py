def poll_subprocess(self):
        clt = self.rpcclt
        if clt is None:
            return
        try:
            response = clt.pollresponse(self.active_seq, wait=0.05)
        except (EOFError, OSError, KeyboardInterrupt):
            # lost connection or subprocess terminated itself, restart
            # [the KBI is from rpc.SocketIO.handle_EOF()]
            if self.tkconsole.closing:
                return
            response = None
            self.restart_subprocess()
        if response:
            self.tkconsole.resetoutput()
            self.active_seq = None
            how, what = response
            console = self.tkconsole.console
            if how == "OK":
                if what is not None:
                    print(repr(what), file=console)
            elif how == "EXCEPTION":
                if self.tkconsole.getvar("<<toggle-jit-stack-viewer>>"):
                    self.remote_stack_viewer()
            elif how == "ERROR":
                errmsg = "pyshell.ModifiedInterpreter: Subprocess ERROR:\n"
                print(errmsg, what, file=sys.__stderr__)
                print(errmsg, what, file=console)
            # we received a response to the currently active seq number:
            try:
                self.tkconsole.endexecuting()
            except AttributeError:  # shell may have closed
                pass
        # Reschedule myself
        if not self.tkconsole.closing:
            self._afterid = self.tkconsole.text.after(
                self.tkconsole.pollinterval, self.poll_subprocess)