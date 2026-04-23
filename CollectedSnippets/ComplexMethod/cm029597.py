def shapesize(self, stretch_wid=None, stretch_len=None, outline=None):
        """Set/return turtle's stretchfactors/outline. Set resizemode to "user".

        Optional arguments:
           stretch_wid : positive number
           stretch_len : positive number
           outline  : positive number

        Return or set the pen's attributes x/y-stretchfactors and/or outline.
        Set resizemode to "user".
        If and only if resizemode is set to "user", the turtle will be displayed
        stretched according to its stretchfactors:
        stretch_wid is stretchfactor perpendicular to orientation
        stretch_len is stretchfactor in direction of turtles orientation.
        outline determines the width of the shapes's outline.

        Examples (for a Turtle instance named turtle):
        >>> turtle.resizemode("user")
        >>> turtle.shapesize(5, 5, 12)
        >>> turtle.shapesize(outline=8)
        """
        if stretch_wid is stretch_len is outline is None:
            stretch_wid, stretch_len = self._stretchfactor
            return stretch_wid, stretch_len, self._outlinewidth
        if stretch_wid == 0 or stretch_len == 0:
            raise TurtleGraphicsError("stretch_wid/stretch_len must not be zero")
        if stretch_wid is not None:
            if stretch_len is None:
                stretchfactor = stretch_wid, stretch_wid
            else:
                stretchfactor = stretch_wid, stretch_len
        elif stretch_len is not None:
            stretchfactor = self._stretchfactor[0], stretch_len
        else:
            stretchfactor = self._stretchfactor
        if outline is None:
            outline = self._outlinewidth
        self.pen(resizemode="user",
                 stretchfactor=stretchfactor, outline=outline)