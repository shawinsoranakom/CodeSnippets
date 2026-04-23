def extent(self):
        """
        Return the extent of this geometry as a 4-tuple, consisting of
        (xmin, ymin, xmax, ymax).
        """
        from .point import Point

        env = self.envelope
        if isinstance(env, Point):
            xmin, ymin = env.tuple
            xmax, ymax = xmin, ymin
        else:
            xmin, ymin = env[0][0]
            xmax, ymax = env[0][2]
        return (xmin, ymin, xmax, ymax)