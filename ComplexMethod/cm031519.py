def runcode(self, code):
        global interruptible
        try:
            self.user_exc_info = None
            interruptible = True
            try:
                exec(code, self.locals)
            finally:
                interruptible = False
        except SystemExit as e:
            if e.args:  # SystemExit called with an argument.
                ob = e.args[0]
                if not isinstance(ob, (type(None), int)):
                    print('SystemExit: ' + str(ob), file=sys.stderr)
            # Return to the interactive prompt.
        except:
            self.user_exc_info = sys.exc_info()  # For testing, hook, viewer.
            if quitting:
                exit()
            if sys.excepthook is sys.__excepthook__:
                print_exception()
            else:
                try:
                    sys.excepthook(*self.user_exc_info)
                except:
                    self.user_exc_info = sys.exc_info()  # For testing.
                    print_exception()
            jit = self.rpchandler.console.getvar("<<toggle-jit-stack-viewer>>")
            if jit:
                self.rpchandler.interp.open_remote_stack_viewer()
        else:
            flush_stdout()