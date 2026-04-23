def teleport(self, x=None, y=None, *, fill_gap: bool = False) -> None:
        """Instantly move turtle to an absolute position.

        Arguments:
        x -- a number      or     None
        y -- a number             None
        fill_gap -- a boolean     This argument must be specified by name.

        call: teleport(x, y)         # two coordinates
        --or: teleport(x)            # teleport to x position, keeping y as is
        --or: teleport(y=y)          # teleport to y position, keeping x as is
        --or: teleport(x, y, fill_gap=True)
                                     # teleport but fill the gap in between

        Move turtle to an absolute position. Unlike goto(x, y), a line will not
        be drawn. The turtle's orientation does not change. If currently
        filling, the polygon(s) teleported from will be filled after leaving,
        and filling will begin again after teleporting. This can be disabled
        with fill_gap=True, which makes the imaginary line traveled during
        teleporting act as a fill barrier like in goto(x, y).

        Example (for a Turtle instance named turtle):
        >>> tp = turtle.pos()
        >>> tp
        (0.00,0.00)
        >>> turtle.teleport(60)
        >>> turtle.pos()
        (60.00,0.00)
        >>> turtle.teleport(y=10)
        >>> turtle.pos()
        (60.00,10.00)
        >>> turtle.teleport(20, 30)
        >>> turtle.pos()
        (20.00,30.00)
        """
        pendown = self.isdown()
        was_filling = self.filling()
        if pendown:
            self.pen(pendown=False)
        if was_filling and not fill_gap:
            self.end_fill()
        new_x = x if x is not None else self._position[0]
        new_y = y if y is not None else self._position[1]
        self._position = Vec2D(new_x, new_y)
        self.pen(pendown=pendown)
        if was_filling and not fill_gap:
            self.begin_fill()