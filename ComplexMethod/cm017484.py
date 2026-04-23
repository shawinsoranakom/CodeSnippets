def __init__(self, *args):
        """
        The initialization function may take an OGREnvelope structure,
        4-element tuple or list, or 4 individual arguments.
        """

        if len(args) == 1:
            if isinstance(args[0], OGREnvelope):
                # OGREnvelope (a ctypes Structure) was passed in.
                self._envelope = args[0]
            elif isinstance(args[0], (tuple, list)):
                # A tuple was passed in.
                if len(args[0]) != 4:
                    raise GDALException(
                        "Incorrect number of tuple elements (%d)." % len(args[0])
                    )
                else:
                    self._from_sequence(args[0])
            else:
                raise TypeError("Incorrect type of argument: %s" % type(args[0]))
        elif len(args) == 4:
            # Individual parameters passed in.
            #  Thanks to ww for the help
            self._from_sequence([float(a) for a in args])
        else:
            raise GDALException("Incorrect number (%d) of arguments." % len(args))

        # Checking the x,y coordinates
        if self.min_x > self.max_x:
            raise GDALException("Envelope minimum X > maximum X.")
        if self.min_y > self.max_y:
            raise GDALException("Envelope minimum Y > maximum Y.")