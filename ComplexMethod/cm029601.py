def _undogoto(self, entry):
        """Reverse a _goto. Used for undo()
        """
        old, new, go_modes, coodata = entry
        drawing, pc, ps, filling = go_modes
        cLI, cL, pl, items = coodata
        screen = self.screen
        if abs(self._position - new) > 0.5:
            print ("undogoto: HALLO-DA-STIMMT-WAS-NICHT!")
        # restore former situation
        self.currentLineItem = cLI
        self.currentLine = cL

        if pl == [(0, 0), (0, 0)]:
            usepc = ""
        else:
            usepc = pc
        screen._drawline(cLI, pl, fill=usepc, width=ps)

        todelete = [i for i in self.items if (i not in items) and
                                       (screen._type(i) == "line")]
        for i in todelete:
            screen._delete(i)
            self.items.remove(i)

        start = old
        if self._speed and screen._tracing == 1:
            diff = old - new
            diffsq = (diff[0]*screen.xscale)**2 + (diff[1]*screen.yscale)**2
            nhops = 1+int((diffsq**0.5)/(3*(1.1**self._speed)*self._speed))
            delta = diff * (1.0/nhops)
            for n in range(1, nhops):
                if n == 1:
                    top = True
                else:
                    top = False
                self._position = new + delta * n
                if drawing:
                    screen._drawline(self.drawingLineItem,
                                     (start, self._position),
                                     pc, ps, top)
                self._update()
            if drawing:
                screen._drawline(self.drawingLineItem, ((0, 0), (0, 0)),
                                               fill="", width=ps)
        # Turtle now at position old,
        self._position = old
        ##  if undo is done during creating a polygon, the last vertex
        ##  will be deleted. if the polygon is entirely deleted,
        ##  creatingPoly will be set to False.
        ##  Polygons created before the last one will not be affected by undo()
        if self._creatingPoly:
            if len(self._poly) > 0:
                self._poly.pop()
            if self._poly == []:
                self._creatingPoly = False
                self._poly = None
        if filling:
            if self._fillpath == []:
                self._fillpath = None
                print("Unwahrscheinlich in _undogoto!")
            elif self._fillpath is not None:
                self._fillpath.pop()
        self._update()