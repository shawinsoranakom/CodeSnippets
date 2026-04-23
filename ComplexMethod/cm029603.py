def _undo(self, action, data):
        """Does the main part of the work for undo()
        """
        if self.undobuffer is None:
            return
        if action == "rot":
            angle, degPAU = data
            self._rotate(-angle*degPAU/self._degreesPerAU)
            self.undobuffer.pop()
        elif action == "stamp":
            stitem = data[0]
            self.clearstamp(stitem)
        elif action == "go":
            self._undogoto(data)
        elif action in ["wri", "dot"]:
            item = data[0]
            self.screen._delete(item)
            self.items.remove(item)
        elif action == "dofill":
            item = data[0]
            self.screen._drawpoly(item, ((0, 0),(0, 0),(0, 0)),
                                  fill="", outline="")
        elif action == "beginfill":
            item = data[0]
            self._fillitem = self._fillpath = None
            if item in self.items:
                self.screen._delete(item)
                self.items.remove(item)
        elif action == "pen":
            TPen.pen(self, data[0])
            self.undobuffer.pop()