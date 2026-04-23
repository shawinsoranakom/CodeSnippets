def _cc(self, args):
        """Convert colortriples to hexstrings.
        """
        if isinstance(args, str):
            return args
        try:
            r, g, b = args
        except (TypeError, ValueError):
            raise TurtleGraphicsError("bad color arguments: %s" % str(args))
        if self.screen._colormode == 1.0:
            r, g, b = [round(255.0*x) for x in (r, g, b)]
        if not ((0 <= r <= 255) and (0 <= g <= 255) and (0 <= b <= 255)):
            raise TurtleGraphicsError("bad color sequence: %s" % str(args))
        return "#%02x%02x%02x" % (r, g, b)