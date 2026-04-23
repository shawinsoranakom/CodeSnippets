def cancel_callback(self, event=None):
        try:
            if self.text.compare("sel.first", "!=", "sel.last"):
                return # Active selection -- always use default binding
        except:
            pass
        if not (self.executing or self.reading):
            self.resetoutput()
            self.interp.write("KeyboardInterrupt\n")
            self.showprompt()
            return "break"
        self.endoffile = False
        self.canceled = True
        if (self.executing and self.interp.rpcclt):
            if self.interp.getdebugger():
                self.interp.restart_subprocess()
            else:
                self.interp.interrupt_subprocess()
        if self.reading:
            self.top.quit()  # exit the nested mainloop() in readline()
        return "break"