def addcmd(self, cmd, execute=True):
        if execute:
            cmd.do(self.delegate)
        if self.undoblock != 0:
            self.undoblock.append(cmd)
            return
        if self.can_merge and self.pointer > 0:
            lastcmd = self.undolist[self.pointer-1]
            if lastcmd.merge(cmd):
                return
        self.undolist[self.pointer:] = [cmd]
        if self.saved > self.pointer:
            self.saved = -1
        self.pointer = self.pointer + 1
        if len(self.undolist) > self.max_undo:
            ##print "truncating undo list"
            del self.undolist[0]
            self.pointer = self.pointer - 1
            if self.saved >= 0:
                self.saved = self.saved - 1
        self.can_merge = True
        self.check_saved()