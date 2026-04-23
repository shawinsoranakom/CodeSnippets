def runcode(self, code):
        "Override base class method"
        if self.tkconsole.executing:
            self.restart_subprocess()
        self.checklinecache()
        debugger = self.debugger
        try:
            self.tkconsole.beginexecuting()
            if not debugger and self.rpcclt is not None:
                self.active_seq = self.rpcclt.asyncqueue("exec", "runcode",
                                                        (code,), {})
            elif debugger:
                debugger.run(code, self.locals)
            else:
                exec(code, self.locals)
        except SystemExit:
            if not self.tkconsole.closing:
                if messagebox.askyesno(
                    "Exit?",
                    "Do you want to exit altogether?",
                    default="yes",
                    parent=self.tkconsole.text):
                    raise
                else:
                    self.showtraceback()
            else:
                raise
        except:
            if use_subprocess:
                print("IDLE internal error in runcode()",
                      file=self.tkconsole.stderr)
                self.showtraceback()
                self.tkconsole.endexecuting()
            else:
                if self.tkconsole.canceled:
                    self.tkconsole.canceled = False
                    print("KeyboardInterrupt", file=self.tkconsole.stderr)
                else:
                    self.showtraceback()
        finally:
            if not use_subprocess:
                try:
                    self.tkconsole.endexecuting()
                except AttributeError:  # shell may have closed
                    pass